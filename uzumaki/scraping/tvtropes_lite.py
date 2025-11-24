"""TVTropes Lite scraper resilient to DOM churn."""
from __future__ import annotations

import logging
from collections import Counter
from typing import List

from bs4 import BeautifulSoup

from uzumaki.cleaning import deduplicate_by, normalize_whitespace
from uzumaki.models import Trope

from .base import BaseAsyncScraper, ScraperError

logger = logging.getLogger(__name__)


class TVTropesLiteScraper(BaseAsyncScraper):
    name = "tvtropes_lite"
    lite_url = "https://tvtropes.org/pmwiki/lite/Anime/Naruto"

    async def fetch(self) -> List[Trope]:
        logger.info("Fetching tropes from TVTropes lite endpoint")
        response = await self.client.get(self.lite_url)
        if response.status_code >= 400:
            raise ScraperError(f"TVTropes lite unavailable: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        tropes = self._parse_sections(soup)
        tropes = deduplicate_by(tropes, lambda trope: trope.name.lower())
        logger.info("Collected %d tropes from TVTropes lite", len(tropes))
        return tropes

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
