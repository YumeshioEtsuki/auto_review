from recognizers.question_detector import detect_questions
from parsers.docx_parser import parse_docx_file

text = parse_docx_file('data/raw/城轨交通企业管理复习题.docx')
qs = detect_questions(text)
q72 = qs[71]
print(f'Q72 ID: {q72["id"]}')
print(f'Q72 stem: {q72["stem"][:150]}')
print(f'Q72 type: {q72["type"]}')
print(f'Q72 options: {q72.get("options", [])}')
