from docx import Document
import re

doc = Document(r'data/raw/城轨交通企业管理复习题.docx')
lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

print('寻找答案行:')
count = 0
for i, line in enumerate(lines):
    if '答案' in line or '参考答案' in line:
        print(f'\n--- 行{i} ---')
        if i > 0:
            print(f'前一行: {lines[i-1][:80]}')
        print(f'答案行: {line[:150]}')
        if i < len(lines) - 1:
            print(f'后一行: {lines[i+1][:80]}')
        count += 1
        if count >= 15:
            break
