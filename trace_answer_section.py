from parsers.docx_parser import parse_docx_file

text = parse_docx_file('data/raw/城轨交通企业管理复习题.docx')
lines = text.split('\n')

# 显示第120-135行附近的内容
for i in range(120, 135):
    line = lines[i]
    # 检查是否匹配答案标记
    import re
    is_answer_header = re.match(r'^\s*(答案|参考答案|答案要点)\s*[:：]', line)
    is_type_header = re.match(r'^[一二三四五六七八九十]+\s*[、，.]', line)
    is_question_num = re.match(r"^\s*[（(]?\s*(\d+)\s*[)）\.、]\s*(.+)", line)
    
    markers = []
    if is_answer_header:
        markers.append("ANSWER_HEADER")
    if is_type_header:
        markers.append("TYPE_HEADER")
    if is_question_num:
        markers.append(f"QUESTION#{is_question_num.group(1)}")
    
    marker_str = f" [{', '.join(markers)}]" if markers else ""
    print(f"Line {i:3d}{marker_str}: {line[:70]}")
