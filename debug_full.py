"""深度调试：完整题目和答案识别流程"""
import sys
from pathlib import Path
from models.question import Question
from recognizers.question_detector import detect_questions
from recognizers.answer_aligner import extract_answers_from_same_text
from parsers.docx_parser import parse_docx_file

# 解析答案文件
answer_text = parse_docx_file("data/raw/城轨交通企业管理复习题.docx")

# 第一步：检测题目
print("=" * 80)
print("第一步：检测题目")
print("=" * 80)

questions_dicts = detect_questions(answer_text)
print(f"\n总共检测到 {len(questions_dicts)} 个题目")
print("\n前30个题目：")
for i, q in enumerate(questions_dicts[:30]):
    print(f"\nQ{q['id']} [{q['type']}]: {q['stem'][:50]}...")
    if q.get('options'):
        print(f"  选项: {q['options'][:2]}")

# 统计题型分布
from collections import Counter
type_count = Counter(q['type'] for q in questions_dicts)
print(f"\n\n题型分布：")
for qtype, count in sorted(type_count.items()):
    print(f"  {qtype}: {count}")

# 第二步：转换为Question对象
print("\n" + "=" * 80)
print("第二步：转换为Question对象")
print("=" * 80)

questions = []
for q_dict in questions_dicts:
    q = Question(
        id=q_dict['id'],
        stem=q_dict['stem'],
        type=q_dict.get('type', 'short'),
        options=q_dict.get('options'),
        answer=None
    )
    questions.append(q)

print(f"转换完成，共 {len(questions)} 个Question对象")

# 第三步：按题型分组
print("\n" + "=" * 80)
print("第三步：按题型分组")
print("=" * 80)

type_groups = {}
type_order = []
for q in questions:
    q_type = q.type or 'short'
    if q_type not in type_groups:
        type_groups[q_type] = []
        type_order.append(q_type)
    type_groups[q_type].append(q)

print(f"分组顺序: {type_order}")
for qtype in type_order:
    print(f"  {qtype}: {len(type_groups[qtype])} 题")

# 第四步：提取答案块
print("\n" + "=" * 80)
print("第四步：提取答案块")
print("=" * 80)

lines = answer_text.splitlines()
answer_blocks = []
import re

i = 0
while i < len(lines):
    line = lines[i].strip()
    
    # 检测答案行开始
    if re.match(r'^(答案|参考答案)\s*[:：]?', line):
        content = re.sub(r'^(答案|参考答案)\s*[:：]?\s*', '', line)
        current_block = content if content else ""
        
        print(f"\n[找到答案块 #{len(answer_blocks)+1}]")
        print(f"  起始行 {i}: '{line[:60]}'")
        
        # 收集后续行
        i += 1
        collected_lines = []
        while i < len(lines):
            next_line = lines[i].strip()
            
            if re.match(r'^(答案|参考答案)\s*[:：]?', next_line):
                print(f"  结束于行 {i}（新答案块）")
                break
            
            if re.match(r'^[一二三四五六七八九十]', next_line):
                print(f"  结束于行 {i}（新题型标记）")
                break
            
            if next_line:
                collected_lines.append(next_line)
                if current_block:
                    current_block += " " + next_line
                else:
                    current_block = next_line
            
            i += 1
        
        if current_block.strip():
            answer_blocks.append(current_block)
            print(f"  内容长度: {len(current_block)} 字符")
            print(f"  内容预览: {current_block[:80]}...")
        
        continue
    
    i += 1

print(f"\n\n总共提取 {len(answer_blocks)} 个答案块")

# 第五步：尝试匹配答案
print("\n" + "=" * 80)
print("第五步：答案块与题型匹配")
print("=" * 80)

for block_idx, q_type in enumerate(type_order):
    if block_idx >= len(answer_blocks):
        print(f"\n{q_type}: [警告] 没有对应答案块（共{len(answer_blocks)}块）")
        continue
    
    answer_text_block = answer_blocks[block_idx]
    questions_of_type = type_groups[q_type]
    
    print(f"\n{q_type} (题型 #{block_idx}, 共{len(questions_of_type)}题)")
    print(f"  答案块预览: {answer_text_block[:80]}...")
    
    # 按题型解析
    if q_type == 'judge':
        matches = re.findall(r'(\d+)\s*[\.、]?\s*([×√对错])', answer_text_block)
    elif q_type == 'choice':
        matches = re.findall(r'(\d+)\s*[\.、]?\s*([A-Ha-h]+)', answer_text_block)
    else:
        matches = re.findall(r'(\d+)\s*[\.、]?\s*([^0-9]+?)(?=\d+\s*[\.、]|$)', answer_text_block)
    
    print(f"  解析结果: 共{len(matches)}个答案")
    if matches:
        print(f"  前5个: {matches[:5]}")
    
    # 尝试匹配
    for seq_str, ans_str in matches[:3]:  # 只显示前3个
        try:
            seq = int(seq_str)
            idx = seq - 1
            if idx < len(questions_of_type):
                q = questions_of_type[idx]
                ans = ans_str.strip().strip('（）() ')
                print(f"    {seq} -> Q{q.id} = '{ans}'")
            else:
                print(f"    {seq} -> [索引越界] idx={idx} >= {len(questions_of_type)}")
        except ValueError:
            print(f"    {seq_str} -> [解析错误]")

# 第六步：调用原始函数
print("\n" + "=" * 80)
print("第六步：调用extract_answers_from_same_text函数")
print("=" * 80)

questions_fresh = []
for q_dict in questions_dicts:
    q = Question(
        id=q_dict['id'],
        stem=q_dict['stem'],
        type=q_dict.get('type', 'short'),
        options=q_dict.get('options'),
        answer=None
    )
    questions_fresh.append(q)

extract_answers_from_same_text(answer_text, questions_fresh)

# 统计有答案的题目
have_answer = sum(1 for q in questions_fresh if q.answer)
print(f"\n提取结果: {have_answer}/{len(questions_fresh)} 有答案")

# 显示各题型的答案情况
for qtype in type_order:
    qs = [q for q in questions_fresh if q.type == qtype]
    have = sum(1 for q in qs if q.answer)
    print(f"  {qtype}: {have}/{len(qs)}")
    # 显示前2个
    for q in qs[:2]:
        if q.answer:
            print(f"    Q{q.id}: {q.answer}")
        else:
            print(f"    Q{q.id}: [无答案]")
