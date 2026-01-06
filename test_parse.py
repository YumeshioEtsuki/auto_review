from parsers.docx_parser import parse_docx_file
from recognizers.question_detector import detect_questions

text = parse_docx_file(r'data\raw\轨道交通运营管理复习题（无答案）.docx')
if text:
    print("=== 文档内容前500字 ===")
    print(text[:500])
    print("\n=== 检测题目 ===")
    qs = detect_questions(text)
    print(f"检测到 {len(qs)} 道题\n")
    for q in qs[:8]:
        print(f"{q['id']}. {q['stem'][:60]}... [{q['type']}] 选项:{q['options'][:2] if q['options'] else 'None'}")
else:
    print("文件读取失败")
