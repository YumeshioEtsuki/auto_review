from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_text_file(path: str) -> Optional[str]:
    file_path = Path(path)
    if not file_path.exists():
        logger.error("Text file not found: %s", path)
        return None
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed for %s, retrying with gbk", path)
        try:
            return file_path.read_text(encoding="gbk")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to read text file %s: %s", path, exc)
            return None
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read text file %s: %s", path, exc)
        return None
