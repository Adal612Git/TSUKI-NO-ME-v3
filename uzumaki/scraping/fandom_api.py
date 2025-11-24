"""MediaWiki API-powered scraper for Naruto Fandom story arcs."""
from __future__ import annotations

import logging
from typing import List

from bs4 import BeautifulSoup

from uzumaki.cleaning import deduplicate_by, normalize_whitespace
from uzumaki.models import StoryArc

from .base import BaseAsyncScraper, ScraperError

logger = logging.getLogger(__name__)


class FandomAPIClient(BaseAsyncScraper):
    name = "fandom_api"
    api_url = "https://naruto.fandom.com/api.php"
    parse_params = {
        "action": "parse",
        "page": "List_of_Story_Arcs",
        "format": "json",
        "prop": "text",
    }

    async def fetch_arcs(self) -> List[StoryArc]:
        logger.info("Fetching story arcs via MediaWiki API")
        response = await self.client.get(self.api_url, params=self.parse_params)
        if response.status_code >= 400:
            raise ScraperError(f"Fandom API unavailable: {response.status_code}")
        payload = response.json()
        html = payload.get("parse", {}).get("text", {}).get("*", "")
        if not html:
            logger.warning("Fandom API response missing parseable HTML")
            return []
        arcs = self._parse_html(html)
        arcs = deduplicate_by(arcs, lambda arc: arc.name.lower())
        logger.info("Collected %d arcs from Fandom API", len(arcs))
        return arcs

    def _parse_html(self, html: str) -> List[StoryArc]:
        soup = BeautifulSoup(html, "html.parser")
        arcs: list[StoryArc] = []
        tables = soup.find_all("table")
        for table in tables:
            headers = [normalize_whitespace(th.text).lower() for th in table.find_all("th")]
            name_idx = self._find_column(headers, {"arc", "story arc", "name"})
            synopsis_idx = self._find_column(headers, {"summary", "synopsis", "description"})
            type_idx = self._find_column(headers, {"type"})
            manga_idx = self._find_column(headers, {"manga chapters", "manga"})
            anime_idx = self._find_column(headers, {"anime episodes", "anime"})
            if name_idx is None:
                continue
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) <= name_idx:
                    continue
                name = normalize_whitespace(cols[name_idx].text)
                if not name:
                    continue
                synopsis = normalize_whitespace(cols[synopsis_idx].text) if synopsis_idx is not None else ""
                arc_type = normalize_whitespace(cols[type_idx].text).lower() if type_idx is not None else ""
                manga_chapters = self._safe_int(cols[manga_idx].text if manga_idx is not None else None)
                anime_episodes = self._safe_int(cols[anime_idx].text if anime_idx is not None else None)
                arcs.append(
                    StoryArc(
                        name=name,
                        start_episode=None,
                        end_episode=None,
                        synopsis=synopsis,
                        is_filler="filler" in arc_type if arc_type else False,
                        manga_chapters=manga_chapters,
                        anime_episodes=anime_episodes,
                    )
                )
        if not arcs:
            logger.warning("No tables with arc data were found in Fandom API response")
        return arcs

    def _find_column(self, headers: list[str], candidates: set[str]) -> int | None:
        for idx, header in enumerate(headers):
            if any(candidate in header for candidate in candidates):
                return idx
        return None

    def _safe_int(self, value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value.strip().split()[0].replace(",", ""))
        except (ValueError, AttributeError):
            return None
