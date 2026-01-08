from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from config import (
    ANSWER_LINE_PATTERN,
    FILL_MARKERS,
    JUDGE_PATTERN,
    OPTION_PATTERN,
    QUESTION_START_PATTERN,
    SECTION_PATTERN,
    SHORT_QUESTION_PREFIXES,
)

logger = logging.getLogger(__name__)

QuestionDict = Dict[str, Optional[str]]


def _detect_type(stem: str, options: List[str], has_multiple_correct: bool = False) -> str:
    """检测题型
    
    Args:
        stem: 题干
        options: 选项列表
        has_multiple_correct: 是否有多个正确答案的标记（用于区分多选题）
    """
    # 判断题检测：题干末尾有 (     ) 或 （     ）
    if JUDGE_PATTERN.search(stem):
        return 'judge'
    
    if options:
        # 如果有4个或更多选项 + 多个正确答案标记，判定为多选题
        if len(options) >= 4 and has_multiple_correct:
            return "multi"
        return "choice"
    if any(marker in stem for marker in FILL_MARKERS):
        return "fill"
    
    # 新增：检测句中单独空格（列车运行题库的填空格式）
    # 1. 汉字+空格+汉字：例如"方向 并"
    # 2. 汉字+空格+标点：例如"产生 ，"（空格在标点前）
    # 3. 引号中的空格：例如"" "" 或 " " - 单独处理
    
    # 先检查引号中是否有空格（通常是填空位置）
    # 支持多种引号：" " "" "" ' '
    if re.search(r'[""\u201c](\s+)[""\u201d]', stem):
        return 'fill'
    
    # 再检查汉字后的空格（排除引号部分）
    temp_stem = re.sub(r'[""\u201c][^"""\u201c\u201d]+[""\u201d]', '', stem)  # 移除引号内容
    if re.search(r'[\u4e00-\u9fff]\s+[\u4e00-\u9fff，。、；：！？）》]', temp_stem):
        return 'fill'
    
    # 检测连续多个空格
    if re.search(r'\s{2,}', stem):
        return 'fill'
    
    if any(stem.strip().startswith(prefix) for prefix in SHORT_QUESTION_PREFIXES):
        return "short"
    return "short"


def detect_questions(text: str, format_info: Optional[Dict] = None) -> List[Dict]:
    """检测题目
    
    Args:
        text: 纯文本内容
        format_info: 格式信息字典 {行号: {'is_strike': bool, 'is_bold': bool, ...}}
    """
    lines = [line.rstrip() for line in text.splitlines()]
    questions: List[Dict] = []
    current: Dict[str, Optional[str]] = {"id": 0, "type": None, "stem": None, "options": [], "emphasis": []}
    question_id = 1
    format_info = format_info or {}

    def commit_current():
        nonlocal question_id, current
        if current.get("stem"):
            # 跳过有删除线的题目
            if current.get("is_strike"):
                logger.debug(f"Skipping question {question_id} (marked with strikethrough)")
                current = {"id": 0, "type": None, "stem": None, "options": [], "emphasis": []}
                return
            
            # 检测是否有多个正确答案的标记
            has_multiple_correct = any(
                "多个" in str(e) or "都对" in str(e) 
                for e in current.get("emphasis", [])
            )
            
            current["id"] = question_id
            current["type"] = _detect_type(
                current.get("stem") or "", 
                current.get("options") or [],
                has_multiple_correct
            )
            questions.append({
                "id": current["id"],
                "type": current["type"],
                "stem": current.get("stem"),
                "options": current.get("options") or None,
                "answer": None,
            })
            question_id += 1
        current = {"id": 0, "type": None, "stem": None, "options": [], "emphasis": [], "is_strike": False}

    line_idx = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            line_idx += 1
            continue
        
        # 获取当前行的格式信息
        line_format = format_info.get(line_idx, {})
        is_strike = line_format.get("is_strike", False)
        is_bold = line_format.get("is_bold", False)
        is_underline = line_format.get("is_underline", False)
        
        # 过滤章节和题型标题
        if SECTION_PATTERN.match(stripped):
            line_idx += 1
            continue
        
        # 跳过答案行（不受格式影响）
        if ANSWER_LINE_PATTERN.search(line):
            line_idx += 1
            continue

        # 识别选项（支持 A. 和 A、，以及同行多选项）
        option_match = OPTION_PATTERN.match(stripped)
        if option_match and current.get("stem"):
            # 先按多空格分割（处理同行多选项，如 "A、答案1   B、答案2"）
            parts = re.split(r'\s{2,}', stripped)
            for part in parts:
                opt_match = re.match(r'^[A-Ha-h][\.|、]\s*(.+)', part.strip())
                if opt_match:
                    opt_text = opt_match.group(1).strip()
                    current["options"].append(opt_text)
                    # 记录下划线的选项（要点标记）
                    if is_underline:
                        current["emphasis"].append(f"option:{opt_text}")
            line_idx += 1
            continue

        # 识别题号（支持 1. 1) 1、）
        question_number_match = re.match(r"^\s*(\d+)[\.|\)、]\s*(.+)", line)
        if question_number_match:
            commit_current()
            stem_text = question_number_match.group(2).strip()
            current["stem"] = stem_text
            current["is_strike"] = is_strike
            # 记录加粗或下划线的题干（重点标记）
            if is_bold or is_underline:
                current["emphasis"].append("stem_marked")
            line_idx += 1
            continue

        # 如果当前有题干，继续追加文本（多行题干）
        if current.get("stem"):
            current["stem"] += " " + stripped
            line_idx += 1
            continue
        
        line_idx += 1

    commit_current()
    return questions
