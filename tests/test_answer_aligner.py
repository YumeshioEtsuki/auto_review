import json
from pathlib import Path

from recognizers.answer_aligner import align_answers

SAMPLE_WITH = """
. Python 的创始人是谁？
A. Bill Gates
B. Guido van Rossum
C. Linus Torvalds
D. Tim Berners-Lee
答案：B

. HTTP 状态码 200 表示______。
答案：请求成功
""".strip()

SAMPLE_WITHOUT = """
. Python 的创始人是谁？
A. Bill Gates
B. Guido van Rossum
C. Linus Torvalds
D. Tim Berners-Lee

. HTTP 状态码 200 表示______。
""".strip()


def test_align_answers_basic(tmp_path: Path):
    questions = align_answers(SAMPLE_WITH, SAMPLE_WITHOUT)
    assert len(questions) == 2
    assert questions[0].answer == "B"
    assert "HTTP" in questions[1].stem
    assert questions[1].answer == "请求成功"


def test_align_answers_missing_answers(tmp_path: Path):
    questions = align_answers(None, SAMPLE_WITHOUT)
    assert len(questions) == 2
    assert all(q.answer is None for q in questions)


def test_align_answers_partial(tmp_path: Path):
    partial_with = SAMPLE_WITH.replace("答案：请求成功", "")
    questions = align_answers(partial_with, SAMPLE_WITHOUT)
    assert len(questions) == 2
    assert questions[0].answer == "B"


def test_json_serialization(tmp_path: Path):
    questions = align_answers(SAMPLE_WITH, SAMPLE_WITHOUT)
    data = [q.model_dump() for q in questions]
    tmp_file = tmp_path / "questions.json"
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    loaded = json.loads(tmp_file.read_text(encoding="utf-8"))
    assert loaded[0]["stem"].startswith("Python")
