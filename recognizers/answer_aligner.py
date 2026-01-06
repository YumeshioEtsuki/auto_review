from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import List, Optional

from config import ANSWER_LINE_PATTERN
from models.question import Question
from recognizers.question_detector import detect_questions

logger = logging.getLogger(__name__)


def _extract_answers_from_text(text: str) -> List[str]:
    answers: List[str] = []
    for line in text.splitlines():
        match = ANSWER_LINE_PATTERN.search(line)
        if match:
            answers.append(match.group(1).strip())
    return answers


def _extract_inline_choice_answers(text: str) -> List[str]:
    """Capture trailing答案字母，如 "1、……。A" / "（ ）。B" / "( ) C"."""
    answers: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        # 匹配行尾单个或多个答案字母（支持多选：ABCD）
        m = re.match(r"^\d+[^\n]*?[。\.）\)]\s*([A-Ha-h]+)\s*$", line)
        if m:
            answers.append(m.group(1).strip())
    return answers


def _extract_fill_answer(stem_with_ans: str, stem_without_ans: str) -> Optional[str]:
    """Extract fill answers; first use bracket capture, fallback to diff."""
    pieces = []
    bracket_matches = re.findall(r"（([^）]+)）|\(([^)]+)\)", stem_with_ans)
    for m1, m2 in bracket_matches:
        val = m1 or m2
        if val:
            pieces.append(val.strip())
    if pieces:
        return "；".join(pieces)

    matcher = SequenceMatcher(None, stem_without_ans, stem_with_ans)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            segment = stem_with_ans[j1:j2].strip()
            if segment:
                segment = segment.strip("（）() ")
                pieces.append(segment)
    if pieces:
        return "；".join(pieces)
    return None


def _align_by_sequence(with_ans_text: str, without_ans_text: str, questions: List[Question]) -> List[Question]:
    matcher = SequenceMatcher(None, without_ans_text, with_ans_text)
    opcodes = matcher.get_opcodes()
    extra_segments: List[str] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "insert":
            extra_segments.append(with_ans_text[j1:j2].strip())
    answers = [seg for seg in extra_segments if seg and len(seg) < 200]
    for idx, ans in enumerate(answers):
        if idx < len(questions) and questions[idx].answer is None:
            questions[idx].answer = ans
    return questions


def align_answers(with_ans_text: Optional[str], without_ans_text: str) -> List[Question]:
    base_questions = [Question(**q) for q in detect_questions(without_ans_text)]

    if with_ans_text:
        extracted = _extract_answers_from_text(with_ans_text)

        # 方案1：显式“答案：”行
        if extracted and len(extracted) == len(base_questions):
            for q, ans in zip(base_questions, extracted):
                q.answer = ans
            return base_questions
        if extracted and len(extracted) <= len(base_questions):
            for idx, ans in enumerate(extracted):
                base_questions[idx].answer = ans

        # 方案2：行尾附字母的选择题（如 “1、……。A”）
        inline_choice = _extract_inline_choice_answers(with_ans_text)
        if inline_choice:
            choice_idxs = [i for i, q in enumerate(base_questions) if q.type == "choice"]
            for ans, idx in zip(inline_choice, choice_idxs):
                base_questions[idx].answer = ans

        # 方案3：按题号对齐后，利用填空题插入差异抽取括号答案
        answered_questions = [Question(**q) for q in detect_questions(with_ans_text)]

        # 优先对等长情形直接按序对齐
        if len(answered_questions) == len(base_questions):
            iterable = zip(base_questions, answered_questions)
        else:
            iterable = []

        for base, answered in iterable:
            if base.answer:
                continue
            if base.type == "fill":
                fill_ans = _extract_fill_answer(answered.stem, base.stem)
                if fill_ans:
                    base.answer = fill_ans
            elif base.type == "choice" and answered.answer:
                base.answer = answered.answer

        # 如果数量不一致或仍有空缺，基于相似度匹配填空题
        if answered_questions:
            remaining = answered_questions.copy()
            for base in base_questions:
                if base.answer or base.type != "fill":
                    continue
                best_idx = -1
                best_score = 0.0
                for idx, cand in enumerate(remaining):
                    score = SequenceMatcher(None, base.stem, cand.stem).ratio()
                    if score > best_score:
                        best_score = score
                        best_idx = idx
                if best_idx >= 0 and best_score >= 0.6:
                    cand = remaining.pop(best_idx)
                    fill_ans = _extract_fill_answer(cand.stem, base.stem)
                    if fill_ans:
                        base.answer = fill_ans

        # 方案4：全局diff兜底
        base_questions = _align_by_sequence(with_ans_text, without_ans_text, base_questions)
        return base_questions

    return base_questions
