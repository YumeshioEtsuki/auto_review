import re
from typing import Pattern

QUESTION_START_PATTERN: Pattern[str] = re.compile(r"^\s*(?:\d+[\.|\)、]\s*)?(.*)")
OPTION_PATTERN: Pattern[str] = re.compile(r"^[A-Ha-h][\.|、]\s*(.+)")
FILL_MARKERS = ["____", "______", "（ ）", "( )", "___", "________"]
SHORT_QUESTION_PREFIXES = ["简述", "解释", "论述", "说明", "为什么", "如何", "什么是", "试述"]
ANSWER_LINE_PATTERN: Pattern[str] = re.compile(r"答案\s*[:：]\s*(.+)")

# 新增：过滤章节和题型标题
SECTION_PATTERN: Pattern[str] = re.compile(r"^第[一二三四五六七八九十\d]+[章节]|^[一二三四五六七八九十]+、.*(题|答案)")

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
