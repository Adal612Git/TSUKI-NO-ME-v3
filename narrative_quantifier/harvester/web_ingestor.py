from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable, List
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass
class WebHarvestResult:
    """Result of fetching a remote narrative source."""

    work_id: str
    url: str
    text: str
    checksum: str


class _TextExtractor(HTMLParser):
    """Minimal HTML → text extractor to avoid heavy dependencies."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip_depth == 0:
            normalized = re.sub(r"\s+", " ", data)
            if normalized.strip():
                self._chunks.append(normalized.strip())

    def get_text(self) -> str:
        return " ".join(self._chunks)


class WebIngestor:
    """Lightweight web scraper focused on narrative sources.

    The implementation favors resilience and a tiny dependency footprint: it
    validates URLs, performs a polite HTTP GET with a custom UA, strips scripts
    and styles, and returns a deterministic checksum to maintain idempotency.
    """

    def __init__(self, user_agent: str = "TSUKI-NO-ME/auto-harvest") -> None:
        self.user_agent = user_agent

    def ingest(self, url: str) -> WebHarvestResult:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported URL scheme for scraping: {url}")

        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request) as response:  # nosec: trusted by caller
            raw_bytes = response.read()
        decoded = raw_bytes.decode("utf-8", errors="replace")
        text = self._extract_text(decoded)
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        work_id = self._slugify(parsed.netloc + parsed.path)
        return WebHarvestResult(work_id=work_id, url=url, text=text, checksum=checksum)

    def batch_ingest(self, urls: Iterable[str]) -> List[WebHarvestResult]:
        results: List[WebHarvestResult] = []
        for url in urls:
            results.append(self.ingest(url))
        return results

    @staticmethod
    def _extract_text(raw_html: str) -> str:
        if "<" not in raw_html or ">" not in raw_html:
            return re.sub(r"\s+", " ", raw_html).strip()
        extractor = _TextExtractor()
        extractor.feed(raw_html)
        return extractor.get_text()

    @staticmethod
    def _slugify(raw: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
        return slug or "web-source"
