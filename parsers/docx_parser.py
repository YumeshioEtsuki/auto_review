from pathlib import Path
from typing import Optional
import logging

from docx import Document

logger = logging.getLogger(__name__)


def parse_docx_file(path: str) -> Optional[str]:
    file_path = Path(path)
    if not file_path.exists():
        logger.error("DOCX file not found: %s", path)
        return None
    try:
        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read DOCX file %s: %s", path, exc)
        return None
