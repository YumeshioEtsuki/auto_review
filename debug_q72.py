from recognizers.question_detector import detect_questions
from parsers.docx_parser import parse_docx_file

text = parse_docx_file('data/raw/城轨交通企业管理复习题.docx')
lines = text.split('\n')

# 显示第72个题号匹配的行
import re
matches = []
for i, line in enumerate(lines):
    question_number_match = re.match(r"^\s*[（(]?\s*(\d+)\s*[)）\.、]\s*(.+)", line)
    if question_number_match:
        seq_num = int(question_number_match.group(1))
        if seq_num == 12:  # 应该是第12题
            matches.append((i, line))

print(f"找到 {len(matches)} 个'12.'开头的行：")
for i, line in matches[:5]:
    print(f"Line {i}: {line[:80]}")

qs = detect_questions(text)
print(f"\n总共检测到 {len(qs)} 个题目")

# 找第72个题目
if len(qs) >= 72:
    q72 = qs[71]
    print(f"\nQ72 (index 71):")
    print(f"  ID: {q72['id']}")
    print(f"  stem: {q72['stem'][:100]}")
    print(f"  type: {q72['type']}")
