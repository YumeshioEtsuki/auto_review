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


def align_answers(with_ans_text: Optional[str], without_ans_text: str) -> List[Question]:
    """对齐答案与题目（按题型分块处理）
    
    核心逻辑：题库答案是按题型分块的
    - 填空题 1-20 的答案在"答案："行
    - 判断题 1-20 的答案在另一个"答案："行
    - ...以此类推
    
    需要按题型分别提取答案块，然后匹配
    """
    base_questions = [Question(**q) for q in detect_questions(without_ans_text)]

    if not with_ans_text:
        return base_questions
    
    # 按题型分组题目
    type_groups = {}
    for q in base_questions:
        q_type = q.type or 'short'
        if q_type not in type_groups:
            type_groups[q_type] = []
        type_groups[q_type].append(q)
    
    with_ans_lines = with_ans_text.splitlines()
    
    # 为每个题型查找并提取对应的答案块
    for q_type, questions_of_type in type_groups.items():
        # 定义题型标记关键词
        type_keywords = {
            'fill': ['填空题', '填空'],
            'judge': ['判断题', '判断'],
            'choice': ['选择题', '选择', '单选题', '单选'],
            'short': ['简答题', '简答', '论述'],
            'comprehensive': ['综合应用题', '综合应用', '综合题', '综合'],
            'case': ['案例分析题', '案例分析', '案例题'],
        }
        
        keywords = type_keywords.get(q_type, [str(q_type)])
        
        # 查找该题型的答案块：找到题型标记后的"答案："行
        answer_start_idx = -1
        for i, line in enumerate(with_ans_lines):
            # 当前行有题型标记（如"二、判断题"）
            if any(kw in line for kw in keywords):
                # 从下一行开始查找"答案："
                for j in range(i + 1, min(i + 5, len(with_ans_lines))):
                    if re.match(r'^\s*答案\s*[:：]?', with_ans_lines[j]):
                        answer_start_idx = j
                        break
                if answer_start_idx > 0:
                    break
        
        if answer_start_idx < 0:
            continue
        
        # 从answer_start_idx开始收集答案行，直到遇到下一个题型或空行
        answer_text = ""
        for i in range(answer_start_idx, len(with_ans_lines)):
            line = with_ans_lines[i].strip()
            if not line:
                continue
            
            # 遇到下一个题型标记，停止
            all_keywords = []
            for kws in type_keywords.values():
                all_keywords.extend(kws)
            
            if i > answer_start_idx:
                has_next_type = any(kw in line for kw in all_keywords)
                if has_next_type:
                    break
            
            answer_text += line + " "
        
        # 解析答案文本："1.xxx 2.xxx 3.xxx..."或"1.× 2.√ ..."
        if answer_text:
            # 处理判断题和填空题的特殊格式
            if q_type == 'judge':
                # 判断题答案可能是"1.× 2.√"或"1.× 2. √"
                matches = re.findall(r'(\d+)\s*[\.、]\s*([×√对错TF])', answer_text)
            else:
                # 其他题型："1.答案 2.答案"
                matches = re.findall(r'(\d+)\s*[\.、]\s*([^0-9]+?)(?=\d+\s*[\.、]|$)', answer_text)
            
            for qid_str, ans_str in matches:
                try:
                    qid = int(qid_str)
                    ans = ans_str.strip().strip('（）() ')
                    # 查找对应ID的题目
                    for q in questions_of_type:
                        if q.id == qid:
                            if not q.answer:
                                q.answer = ans
                            break
                except ValueError:
                    continue
    
    return base_questions
