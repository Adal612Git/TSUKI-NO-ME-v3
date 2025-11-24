"""TVTropes Lite scraper resilient to DOM churn."""
from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path
from collections import Counter
from typing import List

from bs4 import BeautifulSoup

from uzumaki.cleaning import deduplicate_by, normalize_whitespace
from uzumaki.models import Trope

from .base import AsyncCachedClient, BaseAsyncScraper, ScraperError

logger = logging.getLogger(__name__)


class TVTropesLiteScraper(BaseAsyncScraper):
    name = "tvtropes_lite"
    lite_url = "https://tvtropes.org/pmwiki/lite/Anime/Naruto"

    def __init__(self) -> None:
        self._header_pool = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        super().__init__(client=AsyncCachedClient(headers=self._browser_headers(), cookies=self._seed_cookies()))

    async def fetch(self) -> List[Trope]:
        logger.info("Fetching tropes from TVTropes lite endpoint")
        await asyncio.sleep(random.uniform(0.8, 2.4))
        response = await self.client.get(self.lite_url, headers=self._browser_headers())
        if response.status_code in {403, 429, 503}:
            logger.warning("TVTropes blocked request (%s)", response.status_code)
            fallback = self._load_fallback_dataset()
            if fallback:
                return fallback
            raise ScraperError(f"TVTropes lite unavailable: {response.status_code}")
        if response.status_code >= 400:
            raise ScraperError(f"TVTropes lite unavailable: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        tropes = self._parse_sections(soup)
        tropes = deduplicate_by(tropes, lambda trope: trope.name.lower())
        logger.info("Collected %d tropes from TVTropes lite", len(tropes))
        return tropes

    def _load_fallback_dataset(self) -> List[Trope]:
        fallback_path = Path(__file__).resolve().parents[2] / "data" / "tvtropes_fallback.json"
        if fallback_path.exists():
            try:
                data = json.loads(fallback_path.read_text(encoding="utf-8"))
                logger.warning("TVTropes blocked, loading fallback dataset from %s", fallback_path)
                return [
                    Trope(
                        name=item.get("name", ""),
                        category=item.get("category", "General Tropes"),
                        frequency=int(item.get("frequency", 1)),
                    )
                    for item in data
                    if item.get("name")
                ]
            except Exception as exc:  # pragma: no cover - defensive logging only
                logger.warning("Failed to load TVTropes fallback dataset: %s", exc)
        return []

    def _browser_headers(self) -> dict[str, str]:
        user_agent = random.choice(self._header_pool) if hasattr(self, "_header_pool") else None
        return {
            "User-Agent": user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Cache-Control": "no-cache",
        }

    def _seed_cookies(self) -> dict[str, str]:
        return {"session": "naruto-lite"}

    def _parse_sections(self, soup: BeautifulSoup) -> List[Trope]:
        tropes: list[Trope] = []
        headings = soup.find_all(["h1", "h2", "h3", "h4"])
        if headings:
            for heading in headings:
                category = normalize_whitespace(heading.text) or "General Tropes"
                ul = heading.find_next_sibling("ul")
                if not ul:
                    continue
                tropes.extend(self._extract_list_items(ul, category))
        else:
            # fallback: collect every list item on the lite page
            for ul in soup.find_all("ul"):
                tropes.extend(self._extract_list_items(ul, "General Tropes"))
        counter = Counter()
        for trope in tropes:
            counter[(trope.category, trope.name)] += 1
        return [Trope(name=name, category=category, frequency=freq) for (category, name), freq in counter.items()]

    def _extract_list_items(self, ul, category: str) -> List[Trope]:
        items: list[Trope] = []
        for li in ul.find_all("li"):
            title = normalize_whitespace(li.text)
            if title:
                items.append(Trope(name=title, category=category, frequency=1))
        return items
