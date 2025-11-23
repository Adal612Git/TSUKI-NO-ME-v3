from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple


@dataclass
class CleanResult:
    text: str
    checksum: str


def normalize_text(raw_text: str) -> CleanResult:
    """Lightweight normalization for OCR/HTML style noise.

    - Collapses repeated whitespace
    - Removes simple HTML tags
    - Standardizes quotes
    """

    no_tags = re.sub(r"<[^>]+>", " ", raw_text)
    standardized_quotes = no_tags.replace("“", '"').replace("”", '"').replace("’", "'")
    collapsed = re.sub(r"\s+", " ", standardized_quotes).strip()
    checksum = _checksum(collapsed)
    return CleanResult(text=collapsed, checksum=checksum)


def _checksum(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()
