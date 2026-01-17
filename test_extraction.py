from models.question import Question
from recognizers.question_detector import detect_questions
from recognizers.answer_aligner import extract_answers_from_same_text
from parsers.docx_parser import parse_docx_file
import sys
import io

# 设置输出编码为utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

answer_text = parse_docx_file('data/raw/城轨交通企业管理复习题.docx')
questions_dicts = detect_questions(answer_text)
print(f'检测到 {len(questions_dicts)} 个题目')
print(f'Q20: {questions_dicts[19]["stem"][:50]}')
print(f'Q21: {questions_dicts[20]["stem"][:50]}')
print(f'Q22: {questions_dicts[21]["stem"][:50]}')

questions = [Question(id=q['id'], stem=q['stem'], type=q.get('type', 'short'), options=q.get('options'), answer=None) for q in questions_dicts]
extract_answers_from_same_text(answer_text, questions)

have_answer = sum(1 for q in questions if q.answer)
print(f'\n提取结果: {have_answer}/{len(questions)} 有答案')
for qtype in ['fill', 'judge', 'choice', 'short', 'comprehensive', 'case']:
    qs = [q for q in questions if q.type == qtype]
    have = sum(1 for q in qs if q.answer)
    print(f'  {qtype}: {have}/{len(qs)}')
    # 显示前3个无答案的题目
    no_answer_qs = [q for q in qs if not q.answer][:3]
    if no_answer_qs:
        for q in no_answer_qs:
            print(f'    No answer: Q{questions.index(q)+1}: {q.stem[:40]}...')
