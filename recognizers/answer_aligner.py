from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import List, Optional

from config import ANSWER_LINE_PATTERN
from models.question import Question
from recognizers.question_detector import detect_questions

logger = logging.getLogger(__name__)


def align_answers(with_ans_text: Optional[str], without_ans_text: str) -> List[Question]:
    """对齐答案与题目
    
    核心逻辑：
    - 如果提供了两份不同的文本，按题型分块匹配
    - 如果只提供一份文本（或两份相同），直接从"答案："行提取
    """
    base_questions = [Question(**q) for q in detect_questions(without_ans_text)]

    # 如果没有含答案文本，或与纯题干文本相同，则直接提取
    if not with_ans_text or with_ans_text.strip() == without_ans_text.strip():
        # 直接从 without_ans_text 中提取答案块
        extract_answers_from_same_text(without_ans_text, base_questions)
        return base_questions
    
    # 如果有两份不同的文本，按题型分块匹配
    extract_answers_by_type(with_ans_text, base_questions)
    return base_questions


def extract_answers_from_same_text(text: str, questions: List[Question]) -> None:
    """从同一份文本中提取答案（题目和答案在一起）
    
    策略：提取所有答案块，然后尝试将其与各题型的问题进行智能匹配
    不假设题型顺序，而是通过答案内容的特征来确定属于哪种题型
    """
    # 提取答案块
    lines = text.splitlines()
    answer_blocks = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测答案行开始
        if re.match(r'^(答案|参考答案)\s*[:：]?', line):
            # 提取答案行本身的内容（去掉前缀）
            content = re.sub(r'^(答案|参考答案)\s*[:：]?\s*', '', line)
            current_block = content if content else ""
            
            # 收集后续行，直到遇到新的答案标记或新的题型标记
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                
                # 遇到新的"答案："标记，停止当前块
                if re.match(r'^(答案|参考答案)\s*[:：]?', next_line):
                    break
                
                # 遇到题型标记（"一、"、"二、"等），停止
                if re.match(r'^[一二三四五六七八九十]', next_line):
                    break
                
                # 如果下一行非空
                if next_line:
                    if current_block:
                        current_block += " " + next_line
                    else:
                        current_block = next_line
                
                i += 1
            
            # 保存答案块
            if current_block.strip():
                answer_blocks.append(current_block)
            
            continue
        
        i += 1
    
    # 按题型分组问题
    type_groups = {}
    for q in questions:
        q_type = q.type or 'short'
        if q_type not in type_groups:
            type_groups[q_type] = []
        type_groups[q_type].append(q)
    
    # 智能匹配：尝试每个答案块，根据其内容特征判断属于哪种题型，然后应用相应的解析规则
    for answer_block in answer_blocks:
        # 尝试按不同的题型解析答案块，看哪个能解析出合理数量的答案
        
        # 1. 尝试作为判断题答案（×√对错）
        judge_matches = re.findall(r'(\d+)\s*[\.、]?\s*([×√对错])', answer_block)
        # 2. 尝试作为选择题答案（A-H）
        choice_matches = re.findall(r'(\d+)\s*[\.、]?\s*([A-Ha-h]+)', answer_block)
        # 3. 尝试作为其他答案
        other_matches = re.findall(r'(\d+)\s*[\.、]?\s*([^0-9]+?)(?=\d+\s*[\.、]|$)', answer_block)
        
        # 判断这个答案块最可能属于哪种题型
        best_type = None
        best_matches = None
        
        if judge_matches and len(judge_matches) >= 10:
            best_type = 'judge'
            best_matches = judge_matches
        elif choice_matches and len(choice_matches) >= 10:
            best_type = 'choice'
            best_matches = choice_matches
        elif other_matches and len(other_matches) >= 1:
            # 判断是哪种"其他"类型（fill/short/comprehensive/case）
            # 简单策略：看内容长度和内容特征
            avg_len = sum(len(m[1]) for m in other_matches) / len(other_matches)
            
            # 检查是否包含问题-答案的叙述性内容（综合题特征）
            block_text = answer_block.lower()
            if '要点' in block_text or '特点' in block_text or '原因' in block_text or '方案' in block_text or '建议' in block_text:
                # 这是综合/案例题
                best_type = 'comprehensive' if len(answer_block) < 500 else 'case'
            elif avg_len < 15:
                best_type = 'fill'
            elif avg_len < 100:
                best_type = 'short'
            else:
                best_type = 'comprehensive'
            best_matches = other_matches
        
        # 如果成功识别了题型，就应用匹配
        if best_type and best_matches and best_type in type_groups:
            questions_of_type = type_groups[best_type]
            for seq_str, ans_str in best_matches:
                try:
                    seq = int(seq_str)
                    idx = seq - 1
                    if idx < len(questions_of_type):
                        ans = ans_str.strip().strip('（）() ')
                        q = questions_of_type[idx]
                        if not q.answer:
                            q.answer = ans
                except (ValueError, IndexError):
                    continue


def extract_answers_by_type(with_ans_text: str, questions: List[Question]) -> None:
    """从两份不同的文本中按题型分块提取答案"""
    # 按题型分组题目，保持原顺序
    type_groups = {}
    type_order = []
    for q in questions:
        q_type = q.type or 'short'
        if q_type not in type_groups:
            type_groups[q_type] = []
            type_order.append(q_type)
        type_groups[q_type].append(q)
    
    # 提取答案块
    lines = with_ans_text.splitlines()
    answer_blocks = []
    
    current_block = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if re.match(r'^(答案|参考答案)\s*[:：]?', stripped):
            if current_block.strip():
                answer_blocks.append(current_block)
                current_block = ""
            
            content = re.sub(r'^(答案|参考答案)\s*[:：]?\s*', '', stripped)
            current_block = content
        elif current_block and stripped:
            if re.match(r'^\d+[\.、]', stripped) or not re.match(r'^[一二三四五]', stripped):
                current_block += " " + stripped
            else:
                if current_block.strip():
                    answer_blocks.append(current_block)
                    current_block = ""
        elif current_block and not stripped:
            continue
    
    if current_block.strip():
        answer_blocks.append(current_block)
    
    # 按题型匹配
    for block_idx, q_type in enumerate(type_order):
        if block_idx >= len(answer_blocks):
            break
        
        answer_text = answer_blocks[block_idx]
        questions_of_type = type_groups[q_type]
        
        if q_type == 'judge':
            matches = re.findall(r'(\d+)\s*[\.、]\s*([×√对错])', answer_text)
        elif q_type == 'choice':
            matches = re.findall(r'(\d+)\s*[\.、]\s*([A-Ha-h]+)', answer_text)
        else:
            matches = re.findall(r'(\d+)\s*[\.、]?\s*([^0-9]+?)(?=\d+\s*[\.、]|$)', answer_text)
        
        for qid_str, ans_str in matches:
            try:
                qid = int(qid_str)
                ans = ans_str.strip().strip('（）() ')
                for q in questions_of_type:
                    if q.id == qid:
                        if not q.answer:
                            q.answer = ans
                        break
            except ValueError:
                continue
