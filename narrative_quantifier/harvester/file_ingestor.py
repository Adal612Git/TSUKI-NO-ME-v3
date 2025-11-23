from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class HarvesterResult:
    text: str
    checksum: str
    source_path: Optional[Path]


class FileIngestor:
    """Minimal file ingestor that supports text-based sources.

    The implementation is intentionally constrained to keep the repository
    dependency-light while honoring the ETL contract defined in the product
    specification.
    """

    SUPPORTED_SUFFIXES = {".txt", ".md"}

    def ingest(self, path: Path) -> HarvesterResult:
        if path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        text = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return HarvesterResult(text=text, checksum=checksum, source_path=path)
