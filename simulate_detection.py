from parsers.docx_parser import parse_docx_file
import re

text = parse_docx_file('data/raw/城轨交通企业管理复习题.docx')
lines = text.split('\n')

in_answer_section = False

# 模拟检测逻辑
for i in range(120, 135):
    line = lines[i]
    stripped = line.strip()
    
    # 检测答案标记
    answer_header_match = re.match(r'^\s*(答案|参考答案|答案要点)\s*[:：]\s*(.*)$', stripped)
    if answer_header_match:
        content_after = answer_header_match.group(2).strip()
        if len(content_after) < 10:
            in_answer_section = True
            print(f"Line {i}: ENTER answer section")
            continue
    
    # 检测题型标记
    if re.match(r'^[一二三四五六七八九十]+\s*[、，.]', stripped):
        in_answer_section = False
        print(f"Line {i}: EXIT answer section (type header)")
    
    # 检测题号
    question_number_match = re.match(r"^\s*[（(]?\s*(\d+)\s*[)）\.、]\s*(.+)", line)
    if question_number_match:
        seq_num = int(question_number_match.group(1))
        stem_text = question_number_match.group(2).strip()
        
        if in_answer_section:
            # 检查是否退出答案区域
            digit_dot_count = len(re.findall(r'\d+\s*[\.、]', stem_text))
            has_judge_marker = '（ ）' in stem_text or '( )' in stem_text or '（　 ）' in stem_text
            has_question_word = any(w in stem_text for w in ['什么', '哪', '如何', '为什么', '怎样', '多少'])
            is_short_stem = len(stem_text) < 80
            ends_with_question = stem_text.rstrip().endswith(('？', '）', '。'))
            
            is_likely_question = (
                seq_num == 1 or
                has_judge_marker or
                (is_short_stem and digit_dot_count < 2) or
                (has_question_word and digit_dot_count < 2) or
                (ends_with_question and digit_dot_count < 2)
            )
            
            if is_likely_question:
                in_answer_section = False
                print(f"Line {i}: EXIT answer section (likely question) - Q{seq_num}: {stem_text[:50]}")
            else:
                print(f"Line {i}: SKIP (in answer section) - {seq_num}.{stem_text[:40]}")
                continue
        
        print(f"Line {i}: QUESTION Q{seq_num}: {stem_text[:50]}")
