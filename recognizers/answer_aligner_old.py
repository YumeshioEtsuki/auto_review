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


def _extract_inline_indexed_answers(text: str) -> dict[int, str]:
    """提取"答案：1.答案1 2.答案2 3.答案3..."格式的答案
    
    支持跨行答案（如答案分散到多行）
    只使用第一个"答案："标记之后的内容
    
    Returns:
        {题号: 答案} 字典，如 {1: "控制", 2: "外部", ...}
    """
    answer_map = {}
    
    # 找到第一个"答案"行（可有可无冒号）
    lines = text.splitlines()
    start_idx = -1
    for i, line in enumerate(lines):
        if re.match(r'\s*(答案|参考答案)', line):
            start_idx = i
            break
    
    if start_idx == -1:
        return answer_map
    
    # 从该行开始，合并相邻的答案行，直到遇到非答案行
    combined = re.sub(r'^\s*(答案|参考答案)\s*[:：]?\s*', '', lines[start_idx])
    
    for i in range(start_idx + 1, len(lines)):
        next_line = lines[i].strip()
        
        # 如果下一行是答案的延续（以数字开头）且不是新的答案行标记，则合并
        if next_line and next_line[0].isdigit() and not re.match(r'\s*(答案|参考答案)', next_line):
            combined += next_line
        else:
            # 遇到非答案行，停止
            break
    
    # 提取答案对
    matches = re.findall(r'(\d+)\.([^0-9]+?)(?=\d+\.|$)', combined)
    for qid_str, answer in matches:
        qid = int(qid_str)
        answer = answer.strip().strip('（）() ')
        if answer:
            answer_map[qid] = answer
    
    return answer_map


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


def _extract_inline_bracket_answers(text: str) -> dict:
    """提取题干中的内嵌答案，如：（  对  ）、（  错  ）、（  B  ）
    返回 {行号: 答案} 的字典
    """
    answer_map = {}
    lines = text.splitlines()
    
    for idx, line in enumerate(lines):
        # 匹配括号内的答案：（  对  ）、（  B  ）、（错）等
        # 支持全角和半角括号，支持空格
        matches = re.findall(r'[（\(]\s*([对错A-Ha-h]+)\s*[）\)]', line)
        if matches:
            # 取最后一个匹配（通常答案在题干末尾）
            answer_map[idx] = matches[-1].strip()
    
    return answer_map


def _extract_fill_answer(stem_with_ans: str, stem_without_ans: str) -> Optional[str]:
    """Extract fill answers using diff comparison."""
    pieces = []
    
    # 使用diff直接对比无答案版和带答案版，提取差异部分
    matcher = SequenceMatcher(None, stem_without_ans, stem_with_ans)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            segment = stem_with_ans[j1:j2].strip()
            if segment:
                segment = segment.strip("（）() ")
                pieces.append(segment)
        elif tag == "replace":
            # 处理空格被替换为答案的情况（列车运行题库的填空格式）
            # 例如："方向 并" -> "方向相同并"
            replaced_segment = stem_with_ans[j1:j2].strip()
            if replaced_segment and stem_without_ans[i1:i2].strip() == '':
                # 如果被替换的部分是空格，则替换内容就是答案
                pieces.append(replaced_segment)
    if pieces:
        return "；".join(pieces)
    return None
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
        # 方案A：检查是否有"答案：1.xxx 2.xxx 3.xxx..."这种集中答案行
        inline_indexed_answers = _extract_inline_indexed_answers(with_ans_text)
        if inline_indexed_answers:
            for q in base_questions:
                if q.id in inline_indexed_answers:
                    q.answer = inline_indexed_answers[q.id]
            return base_questions
        
        # 方案0：优先提取内嵌括号答案（如：（  对  ）、（  B  ）)
        bracket_answers = _extract_inline_bracket_answers(with_ans_text)
        if bracket_answers:
            with_ans_lines = with_ans_text.splitlines()
            for q in base_questions:
                # 只为判断题匹配括号答案
                if q.type == 'judge' and q.stem:
                    # 在含答案文本中找到这道题的题干
                    for line_idx, line in enumerate(with_ans_lines):
                        if q.stem[:min(20, len(q.stem))] in line:
                            if line_idx in bracket_answers:
                                q.answer = bracket_answers[line_idx]
                                break
        
        extracted = _extract_answers_from_text(with_ans_text)

        # 方案1：显式“答案：”行
        if extracted and len(extracted) == len(base_questions):
            for q, ans in zip(base_questions, extracted):
                if not q.answer:  # 不覆盖已有的内嵌答案
                    q.answer = ans
            return base_questions
        if extracted and len(extracted) <= len(base_questions):
            for idx, ans in enumerate(extracted):
                if not base_questions[idx].answer:
                    base_questions[idx].answer = ans

        # 方案2：行尾附字母的选择题（如 “1、……。A”）
        inline_choice = _extract_inline_choice_answers(with_ans_text)
        if inline_choice:
            choice_idxs = [i for i, q in enumerate(base_questions) if q.type == "choice" and not q.answer]
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
