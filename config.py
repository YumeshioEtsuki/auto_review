import re
from typing import Pattern

QUESTION_START_PATTERN: Pattern[str] = re.compile(r"^\s*(?:\d+[\.|\)、]\s*)?(.*)")
OPTION_PATTERN: Pattern[str] = re.compile(r"^[A-Ha-h][\.|、]\s*(.+)")
FILL_MARKERS = ["____", "______", "（ ）", "( )", "___", "________"]
SHORT_QUESTION_PREFIXES = ["简述", "解释", "论述", "说明", "为什么", "如何", "什么是", "试述"]
ANSWER_LINE_PATTERN: Pattern[str] = re.compile(r"答案\s*[:：]\s*(.+)")

# 多选题的关键词标记（答案行中出现这些词时，判定为多选题）
MULTI_CHOICE_KEYWORDS = ["多个", "都对", "均正确", "都正确", "全选", "皆正确", "全对"]

# 新增：过滤章节和题型标题
SECTION_PATTERN: Pattern[str] = re.compile(r"^第[一二三四五六七八九十\d]+[章节]|^[一二三四五六七八九十]+、.*(题|答案)")

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

