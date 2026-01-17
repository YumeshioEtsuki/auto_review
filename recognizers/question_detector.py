from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from config import (
    ANSWER_LINE_PATTERN,
    CASE_KEYWORDS,
    COMPREHENSIVE_KEYWORDS,
    FILL_MARKERS,
    JUDGE_PATTERN,
    MULTI_CHOICE_KEYWORDS,
    MULTI_STEM_KEYWORDS,
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
        has_multiple_correct: 是否有多个正确答案的标记（目前不单独返回multi，都归为choice）
    """
    # 优先检查：如果有选项（A/B/C/D等），则必然是选择题，不论题干格式如何
    if options and len(options) >= 2:
        return "choice"
    
    # 判断题检测：题干中含有"（）"或"( )"且没有选项
    if JUDGE_PATTERN.search(stem):
        return 'judge'
    
    stem_lower = stem.lower()
    
    if any(marker in stem for marker in FILL_MARKERS):
        return "fill"

    # 综合/案例类优先识别（含长度兜底增强）
    if any(keyword.lower() in stem_lower for keyword in COMPREHENSIVE_KEYWORDS):
        return "comprehensive"
    if any(keyword.lower() in stem_lower for keyword in CASE_KEYWORDS):
        return "case"
    
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

    # 语义关键词辅助判断
    if any(keyword.lower() in stem_lower for keyword in CASE_KEYWORDS):
        return "case"
    if any(keyword.lower() in stem_lower for keyword in COMPREHENSIVE_KEYWORDS):
        return "comprehensive"

    # 题干长度兜底：长段落优先认为是综合/案例，避免误判为简答
    if len(stem) >= 120:
        if "案例" in stem or "情景" in stem or "情境" in stem:
            return "case"
        return "comprehensive"

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

            stem_text = current.get("stem") or ""

            # 若这是答案行（以“答案/参考答案”开头），跳过，不计入题目
            if stem_text.lstrip().startswith(("答案", "参考答案")):
                current = {"id": 0, "type": None, "stem": None, "options": [], "emphasis": [], "is_strike": False}
                return

            # 处理单行串联多题（如 "7.xxx 8.xxx 9.xxx"），避免题号跳过导致答案错位
            embedded_nums = list(re.finditer(r"(?<!^)(?:\s|　)+(\d{1,3})[\.、]\s*", stem_text))
            if embedded_nums and not current.get("options"):
                parts = []
                last_idx = 0
                for m in embedded_nums:
                    parts.append(stem_text[last_idx:m.start()].strip())
                    last_idx = m.start()
                parts.append(stem_text[last_idx:].strip())
                # 清理空片段
                parts = [p for p in parts if p]
                if len(parts) >= 2:
                    for part in parts:
                        q_type = _detect_type(part, [], has_multiple_correct)
                        questions.append({
                            "id": question_id,
                            "type": q_type,
                            "stem": part,
                            "options": None,
                            "answer": None,
                        })
                        question_id += 1
                    current = {"id": 0, "type": None, "stem": None, "options": [], "emphasis": [], "is_strike": False}
                    return
            
            current["id"] = question_id
            current["type"] = _detect_type(
                stem_text, 
                current.get("options") or [],
                has_multiple_correct
            )
            questions.append({
                "id": current["id"],
                "type": current["type"],
                "stem": stem_text,
                "options": current.get("options") or None,
                "answer": None,
            })
            question_id += 1
        current = {"id": 0, "type": None, "stem": None, "options": [], "emphasis": [], "is_strike": False}

    line_idx = 0
    in_answer_section = False  # 标记是否在答案区域内
    
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
        # 区分两种情况：
        # 1. "答案："或"答案要点："独立一行（后面几乎没内容） - 进入答案区域模式
        # 2. "答案：xxx"（后面有内容） - 只跳过这一行，不进入答案区域
        answer_header_match = re.match(r'^\s*(答案|参考答案|答案要点)\s*[:：]\s*(.*)$', stripped)
        if answer_header_match:
            content_after = answer_header_match.group(2).strip()
            if len(content_after) < 10:  # 内容很少，视为独立的答案块开始
                in_answer_section = True  # 进入答案区域
            line_idx += 1
            continue
        
        # 检测题型标记（"一、"、"二、"等），退出答案区域
        if re.match(r'^[一二三四五六七八九十]+\s*[、，.]', stripped):
            in_answer_section = False  # 新题型开始，退出答案区域

        # 识别选项（支持 A. 和 A、，以及同行多选项）
        option_match = OPTION_PATTERN.match(stripped)
        if option_match and current.get("stem"):
            # 支持同行多选项：用前瞻在每个选项前切分
            parts = re.split(r'(?=[A-Ha-h][\.、．\)）])', stripped)
            for part in parts:
                seg = part.strip()
                if not seg:
                    continue
                opt_match = re.match(r'^[A-Ha-h][\.、．\)）]\s*(.+)', seg)
                if opt_match:
                    opt_text = opt_match.group(1).strip()
                    current["options"].append(opt_text)
                    # 记录下划线的选项（要点标记）
                    if is_underline:
                        current["emphasis"].append(f"option:{opt_text}")
            line_idx += 1
            continue

        # 识别题号（支持 1. 1) 1、）
        question_number_match = re.match(r"^\s*[（(]?\s*(\d+)\s*[)）\.、]\s*(.+)", line)
        if question_number_match:
            stem_text = question_number_match.group(2).strip()
            seq_num = int(question_number_match.group(1))
            
            # 如果在答案区域内，检查是否应该退出答案区域
            if in_answer_section:
                # 判断是否是真正的新题目（而不是答案内容）
                # 答案内容特征：
                # - 包含多个"数字."（连续要点）
                # - 很长的陈述句
                # - 包含"应对"、"思路"、"举措"等答案关键词
                # 
                # 题目特征：
                # - 包含判断题标记"（ ）"
                # - 包含疑问词且较短
                # - 末尾是"？"且不包含多个数字点
                digit_dot_count = len(re.findall(r'\d+\s*[\.、]', stem_text))
                has_judge_marker = '（ ）' in stem_text or '( )' in stem_text or '（　 ）' in stem_text
                has_question_word = any(w in stem_text for w in ['什么', '哪', '如何', '为什么', '怎样', '多少', '简述', '试述', '论述'])
                is_short_stem = len(stem_text) < 60
                ends_with_question = stem_text.rstrip().endswith('？')
                has_answer_keyword = any(w in stem_text for w in ['应对', '思路', '举措', '要点', '特点', '含义', '体现'])
                
                # 明确的题目标记（优先级最高）
                if has_judge_marker or (ends_with_question and is_short_stem):
                    # 判断题或短疑问句，肯定是新题目
                    in_answer_section = False
                # 模糊情况：结合多个特征判断
                elif digit_dot_count >= 2 or has_answer_keyword:
                    # 包含多个数字点或答案关键词，可能是答案内容，跳过
                    line_idx += 1
                    continue
            
            # 额外检查：如果题干本身包含太多个"数字.内容"对，像是答案行而不是题干
            # 答案行特征：连续的 "1.xxx 2.xxx 3.xxx ..." 至少5个
            digit_dot_count = len(re.findall(r'\d+\s*[\.、]', stem_text))
            if digit_dot_count >= 5:
                # 这看起来更像答案行而不是题干，跳过
                line_idx += 1
                continue
            
            commit_current()
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
