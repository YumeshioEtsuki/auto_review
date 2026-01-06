from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from config import (
    ANSWER_LINE_PATTERN,
    FILL_MARKERS,
    OPTION_PATTERN,
    QUESTION_START_PATTERN,
    SECTION_PATTERN,
    SHORT_QUESTION_PREFIXES,
)

logger = logging.getLogger(__name__)

QuestionDict = Dict[str, Optional[str]]


def _detect_type(stem: str, options: List[str]) -> str:
    if options:
        return "choice"
    if any(marker in stem for marker in FILL_MARKERS):
        return "fill"
    if any(stem.strip().startswith(prefix) for prefix in SHORT_QUESTION_PREFIXES):
        return "short"
    return "short"


def detect_questions(text: str) -> List[Dict]:
    lines = [line.rstrip() for line in text.splitlines()]
    questions: List[Dict] = []
    current: Dict[str, Optional[str]] = {"id": 0, "type": None, "stem": None, "options": []}
    question_id = 1

    def commit_current():
        nonlocal question_id, current
        if current.get("stem"):
            current["id"] = question_id
            current["type"] = _detect_type(current.get("stem") or "", current.get("options") or [])
            questions.append({
                "id": current["id"],
                "type": current["type"],
                "stem": current.get("stem"),
                "options": current.get("options") or None,
                "answer": None,
            })
            question_id += 1
        current = {"id": 0, "type": None, "stem": None, "options": []}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # 过滤章节和题型标题
        if SECTION_PATTERN.match(stripped):
            continue
        
        # 跳过答案行
        if ANSWER_LINE_PATTERN.search(line):
            continue

        # 识别选项（支持 A. 和 A、，以及同行多选项）
        option_match = OPTION_PATTERN.match(stripped)
        if option_match and current.get("stem"):
            # 先按多空格分割（处理同行多选项，如 "A、答案1   B、答案2"）
            parts = re.split(r'\s{2,}', stripped)
            for part in parts:
                opt_match = re.match(r'^[A-Ha-h][\.|、]\s*(.+)', part.strip())
                if opt_match:
                    current["options"].append(opt_match.group(1).strip())
            continue

        # 识别题号（支持 1. 1) 1、）
        question_number_match = re.match(r"^\s*(\d+)[\.|\)、]\s*(.+)", line)
        if question_number_match:
            commit_current()
            current["stem"] = question_number_match.group(2).strip()
            continue

        # 续接题干
        if current.get("stem") and stripped:
            # 避免把下一题的编号误接进来
            if not re.match(r"^\d+[\.|\)、]", stripped):
                current["stem"] += " " + stripped

    commit_current()
    return questions
