import re
from typing import Pattern

QUESTION_START_PATTERN: Pattern[str] = re.compile(r"^\s*(?:[（(]?\s*\d+\s*[)）\.、]\s*)?(.*)")
OPTION_PATTERN: Pattern[str] = re.compile(r"^[A-Ha-h][\.、．\)）]\s*(.+)")
FILL_MARKERS = ["____", "______", "（ ）", "( )", "___", "________"]
SHORT_QUESTION_PREFIXES = ["简述", "解释", "论述", "说明", "为什么", "如何", "什么是", "试述"]
# 综合/案例类题型关键词（命中任意即判定）
COMPREHENSIVE_KEYWORDS = [
	"综合应用",
	"综合题",
	"综合应用题",
	"综合运用",
	"综合性",
	"综合案例",
	"综合训练",
	"综合练习",
	"综合分析",
]
CASE_KEYWORDS = [
	"案例分析",
	"案例题",
	"案例",
	"情景题",
	"情境题",
	"情景分析",
	"案例背景",
	"阅读下列材料",
	"阅读以下材料",
]
MULTI_STEM_KEYWORDS = ["多选", "多项", "不定项", "至少选", "至少选择", "选出所有", "至少两项"]
ANSWER_LINE_PATTERN: Pattern[str] = re.compile(r"(?:答案|参考答案)\s*[:：\s]\s*(.+)")

# 判断题标记：含有空括号"（）"或"( )"（通常在题干开头但前面可能有序号），不含选项A/B/C/D
JUDGE_PATTERN: Pattern[str] = re.compile(r'[（\(]\s*[）\)]')

# 多选题的关键词标记（答案行中出现这些词时，判定为多选题）
MULTI_CHOICE_KEYWORDS = ["多个", "都对", "均正确", "都正确", "全选", "皆正确", "全对"]

# 新增：过滤章节和题型标题
SECTION_PATTERN: Pattern[str] = re.compile(r"^第[一二三四五六七八九十\d]+[章节]|^[一二三四五六七八九十]+、.*(题|答案)")

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

