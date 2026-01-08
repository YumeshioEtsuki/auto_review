import json
import re
from pathlib import Path
import sys
import streamlit as st

# 添加父目录到路径以导入模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parsers.text_parser import parse_text_file
from parsers.docx_parser import parse_docx_file
from recognizers.answer_aligner import align_answers

st.set_page_config(page_title="AutoReview", page_icon="📚", layout="wide")


def normalize_tokens(text: str) -> list[str]:
    if not text:
        return []
    text = str(text).strip().strip("（）() ")
    text = text.replace("；", ";").replace("，", ",")
    parts = re.split(r"[;，,、/\s]+", text)
    return [p.strip().lower() for p in parts if p.strip()]


def _letters_to_options(letters: list[str], options: list[str]) -> list[str]:
    mapped = []
    for ch in letters:
        idx = ord(ch.upper()) - ord("A")
        if 0 <= idx < len(options):
            mapped.append(options[idx].strip().lower())
    return mapped


def evaluate_answer(q_type: str, user_ans, correct_ans: str, options: list[str] | None = None):
    correct_tokens = normalize_tokens(correct_ans)
    # 无标准答案
    if not correct_tokens:
        return None

    if q_type == "choice":
        user_token = normalize_tokens(user_ans)
        if options and all(len(tok) == 1 and tok.isalpha() for tok in correct_tokens):
            target = set(_letters_to_options(correct_tokens, options))
            return bool(user_token) and user_token[0] in target
        return bool(user_token) and user_token[0] in correct_tokens

    if q_type == "judge":
        user_token = normalize_tokens(user_ans)
        # 统一映射：正确/对/√/T -> 对，错误/错/×/F -> 错
        if user_token:
            first = user_token[0]
            if first in ['正确', '对', '√', 't', 'true', 'yes']:
                user_token = ['对']
            elif first in ['错误', '错', '×', 'f', 'false', 'no']:
                user_token = ['错']
        return bool(user_token) and user_token[0] in correct_tokens

    if q_type == "multi":
        user_tokens = normalize_tokens(" ".join(user_ans) if isinstance(user_ans, list) else user_ans)
        if options and all(len(tok) == 1 and tok.isalpha() for tok in correct_tokens):
            target = set(_letters_to_options(correct_tokens, options))
            return set(user_tokens) == target
        return set(user_tokens) == set(correct_tokens)

    if q_type == "fill":
        user_tokens = normalize_tokens(user_ans)
        # 允许用户回答包含所有正确片段即可
        return all(tok in "".join(user_tokens) or tok in str(user_ans) for tok in correct_tokens)

    # short / calc 不判分
    return None

# 侧边栏：文件选择和生成
with st.sidebar:
    st.header("📁 题库管理")
    if "wrong_book" not in st.session_state:
        st.session_state.wrong_book = []
    if "auto_next" not in st.session_state:
        st.session_state.auto_next = True

    st.checkbox("判对后自动跳下一题", key="auto_next")
    
    mode = st.radio("选择输入方式", ["从文件夹选择", "直接上传文件"])
    
    if mode == "从文件夹选择":
        raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        available_files = sorted([f.name for f in raw_dir.glob("*.txt")] + 
                                [f.name for f in raw_dir.glob("*.docx")])
        
        if not available_files:
            st.warning("data/raw/ 文件夹为空，请添加复习题文件")
            st.stop()
        
        with_ans_file = st.selectbox("含答案文档", ["(可选)"] + available_files, index=0)
        without_ans_file = st.selectbox("纯题干文档", available_files, index=0)
        
        if st.button("🚀 生成题库", type="primary"):
            with_path = None if with_ans_file == "(可选)" else str(raw_dir / with_ans_file)
            without_path = str(raw_dir / without_ans_file)
            
            with st.spinner("解析中..."):
                def load_file(path):
                    if not path:
                        return None
                    suffix = Path(path).suffix.lower()
                    return parse_text_file(path) if suffix == ".txt" else parse_docx_file(path)
                
                without_text = load_file(without_path)
                with_text = load_file(with_path)
                
                if without_text:
                    questions = align_answers(with_text, without_text)
                    st.session_state.questions = [q.model_dump() for q in questions]
                    st.session_state.idx = 0
                    st.success(f"✓ 成功加载 {len(questions)} 道题")
                    st.rerun()
                else:
                    st.error("文件解析失败")
    
    else:  # 上传文件
        with_upload = st.file_uploader("上传含答案文档", type=["txt", "docx"])
        without_upload = st.file_uploader("上传纯题干文档", type=["txt", "docx"], key="without")
        
        if st.button("🚀 生成题库", type="primary") and without_upload:
            with st.spinner("解析中..."):
                import tempfile
                
                def load_upload(upload_obj):
                    if not upload_obj:
                        return None
                    with tempfile.NamedTemporaryFile(delete=False, suffix=upload_obj.name) as tmp:
                        tmp.write(upload_obj.read())
                        tmp_path = tmp.name
                    suffix = Path(tmp_path).suffix.lower()
                    text = parse_text_file(tmp_path) if suffix == ".txt" else parse_docx_file(tmp_path)
                    Path(tmp_path).unlink()
                    return text
                
                without_text = load_upload(without_upload)
                with_text = load_upload(with_upload)
                
                if without_text:
                    questions = align_answers(with_text, without_text)
                    st.session_state.questions = [q.model_dump() for q in questions]
                    st.session_state.idx = 0
                    st.success(f"✓ 成功加载 {len(questions)} 道题")
                    st.rerun()
                else:
                    st.error("文件解析失败")

    with st.expander("📒 错题本", expanded=False):
        st.write(f"共 {len(st.session_state.wrong_book)} 条")
        if st.session_state.wrong_book:
            for item in st.session_state.wrong_book:
                st.markdown(f"**第 {item['id']} 题 ({item['type']})** - {item['stem']}")
                st.markdown(f"你的答案：{item['user_answer']}")
                st.markdown(f"正确答案：{item['answer']}")
                st.divider()
            if st.button("清空错题本"):
                st.session_state.wrong_book = []
                st.rerun()

# 主界面：题目展示
st.title("AutoReview 互动练习")

if "questions" not in st.session_state:
    # 尝试加载默认JSON
    default_json = Path(__file__).resolve().parent.parent / "data" / "processed" / "questions.json"
    if default_json.exists():
        with default_json.open("r", encoding="utf-8") as f:
            st.session_state.questions = json.load(f)
            st.session_state.idx = 0
    else:
        st.info("👈 请在左侧选择或上传复习题文件")
        st.stop()

questions = st.session_state.questions

if "idx" not in st.session_state:
    st.session_state.idx = 0

question = questions[st.session_state.idx]
q_type = question.get("type") or "short"

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"第 {question['id']} 题 ({q_type})")
with col2:
    st.metric("进度", f"{st.session_state.idx + 1}/{len(questions)}")

# 显示题干，填空题中的空格用下划线标记
stem_text = question.get("stem")
if q_type == "fill" and stem_text:
    # 将句中的单独空格或引号中的空格替换为下划线
    stem_text = re.sub(r'[""](\s+)[""]', ' **______** ', stem_text)  # 引号中的空格
    stem_text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff，。、；：！？）》])', r'\1 **______** \2', stem_text)  # 汉字间的空格
    st.markdown(stem_text)
else:
    st.write(stem_text)

user_key = f"user_answer_{question['id']}"

with st.form(key=f"form_{question['id']}"):
    user_answer = st.session_state.get(user_key)

    if q_type == "choice":
        options = question.get("options") or []
        user_answer = st.radio("请选择：", options, key=user_key)
    elif q_type == "multi":
        options = question.get("options") or []
        user_answer = st.multiselect("多选题：", options, key=user_key)
    elif q_type == "fill":
        user_answer = st.text_input("填写答案：", key=user_key)
    elif q_type == "judge":
        user_answer = st.radio("判断题：", ["对", "错"], key=user_key)
    else:
        user_answer = st.text_area("作答：", key=user_key)

    submitted = st.form_submit_button("提交/判题 (Enter)")

    if submitted:
        result = evaluate_answer(q_type, user_answer, question.get("answer"), question.get("options"))
        if result is True:
            st.success("✓ 回答正确！")
        elif result is False:
            st.error("✗ 回答错误")
            if st.checkbox("加入错题本", key=f"wrong_{question['id']}"):
                entry = {
                    "id": question.get("id"),
                    "type": q_type,
                    "stem": question.get("stem"),
                    "answer": question.get("answer"),
                    "user_answer": user_answer,
                }
                if entry not in st.session_state.wrong_book:
                    st.session_state.wrong_book.append(entry)
        else:
            st.info("ℹ 本题不自动判分，参考答案见下方。")

if st.button("显示答案", key=f"show_{question['id']}"):
    st.info(f"**答案/思路：** {question.get('answer') or '暂无答案'}")

# 导航区
st.divider()
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("⬅️ 上一题", use_container_width=True):
        st.session_state.idx = max(0, st.session_state.idx - 1)
        st.rerun()
with col2:
    if st.button("下一题 ➡️", use_container_width=True):
        st.session_state.idx = min(len(questions) - 1, st.session_state.idx + 1)
        st.rerun()
with col3:
    jump_to = st.number_input("跳转到第", min_value=1, max_value=len(questions), value=st.session_state.idx + 1, key="jump")
    if st.button("GO", use_container_width=True):
        st.session_state.idx = jump_to - 1
        st.rerun()
