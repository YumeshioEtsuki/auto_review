from pathlib import Path
from typing import Optional, Dict, Any
import logging

from docx import Document

logger = logging.getLogger(__name__)


class FormattedParagraph:
    """表示带格式信息的段落"""
    def __init__(self, text: str, is_bold: bool = False, is_strike: bool = False, is_underline: bool = False):
        self.text = text
        self.is_bold = is_bold  # 加粗 = 重点
        self.is_strike = is_strike  # 删除线 = 删除这题
        self.is_underline = is_underline  # 下划线 = 要点


def parse_docx_file(path: str) -> Optional[str]:
    """解析DOCX文件，返回纯文本（格式信息丢失）"""
    file_path = Path(path)
    if not file_path.exists():
        logger.error("DOCX file not found: %s", path)
        return None
    try:
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.error("Failed to read DOCX file %s: %s", path, exc)
        return None


def parse_docx_file_with_format(path: str) -> Optional[list[FormattedParagraph]]:
    """解析DOCX文件，保留格式信息（加粗/删除线/下划线）"""
    file_path = Path(path)
    if not file_path.exists():
        logger.error("DOCX file not found: %s", path)
        return None
    try:
        doc = Document(str(file_path))
        formatted_paras = []
        
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            
            # 检测段落级别的格式
            is_para_bold = False
            is_para_strike = False
            is_para_underline = False
            
            # 遍历所有 runs (文本块)
            for run in para.runs:
                if run.bold:
                    is_para_bold = True
                if run.font.strike:
                    is_para_strike = True
                if run.underline:
                    is_para_underline = True
            
            formatted_para = FormattedParagraph(
                text=para.text,
                is_bold=is_para_bold,
                is_strike=is_para_strike,
                is_underline=is_para_underline
            )
            formatted_paras.append(formatted_para)
        
        return formatted_paras
    except Exception as exc:
        logger.error("Failed to read DOCX file %s: %s", path, exc)
        return None

