import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from config import LOG_FORMAT
from parsers.docx_parser import parse_docx_file
from parsers.text_parser import parse_text_file
from recognizers.answer_aligner import align_answers

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def load_file(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    suffix = Path(path).suffix.lower()
    if suffix == ".txt":
        return parse_text_file(path)
    if suffix == ".docx":
        return parse_docx_file(path)
    logger.error("Unsupported file type: %s", suffix)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="AutoReview CLI - 智能复习题生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                              # 使用默认路径
  python main.py --without-answers my.txt     # 仅指定题干文件
  python main.py --with-answers qa.txt --without-answers q.txt --output out.json
        """
    )
    parser.add_argument(
        "--with-answers",
        dest="with_answers",
        default="./data/raw/questions_with_answers.txt",
        help="含答案文档路径（默认: data/raw/questions_with_answers.txt）"
    )
    parser.add_argument(
        "--without-answers",
        dest="without_answers",
        default="./data/raw/questions_without_answers.txt",
        help="纯题干文档路径（默认: data/raw/questions_without_answers.txt）"
    )
    parser.add_argument(
        "--output",
        dest="output",
        default="./data/processed/questions.json",
        help="输出 JSON 路径（默认: data/processed/questions.json）"
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="仅导出 JSON，不启动 Streamlit 界面（默认会自动启动）"
    )

    args = parser.parse_args()

    logger.info("输入文件（含答案）: %s", args.with_answers)
    logger.info("输入文件（纯题干）: %s", args.without_answers)
    logger.info("输出路径: %s", args.output)

    without_text = load_file(args.without_answers)
    if without_text is None:
        logger.error("无法加载纯题干文件: %s（请检查路径或在 data/raw/ 下创建示例文件）", args.without_answers)
        return

    with_text = load_file(args.with_answers)
    if with_text is None:
        logger.warning("未找到含答案文件，将仅使用纯题干文件提取题目（答案字段为空）")
    questions = align_answers(with_text, without_text)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([q.model_dump() for q in questions], ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("✓ 成功导出 %d 道题目到 %s", len(questions), output_path)
    logger.info("运行 Streamlit 查看: streamlit run ui/streamlit_app.py")

    if not args.no_ui:
        logger.info("正在启动 Streamlit 界面...")
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/streamlit_app.py"], check=True)
        except subprocess.CalledProcessError as exc:  # noqa: PERF203
            logger.error("启动 Streamlit 失败: %s", exc)
        except KeyboardInterrupt:
            logger.info("用户停止了应用")


if __name__ == "__main__":
    main()
