"""Scraper for Naruto Fandom Wiki story arcs."""
from __future__ import annotations

import logging
from typing import List

import pandas as pd
from bs4 import BeautifulSoup

from .base import respectful_get
from ..models import StoryArc

logger = logging.getLogger(__name__)


class FandomScraper:
    url = "https://naruto.fandom.com/wiki/List_of_Story_Arcs"

    def fetch(self) -> List[StoryArc]:
        logger.info("Fetching story arcs from Fandom")
        response = respectful_get(self.url)

        try:
            frames = pd.read_html(response.text)
        except (ValueError, ImportError):
            frames = []

        if frames:
            return self._parse_with_pandas(frames)
        return self._parse_manually(response.text)

    def _parse_with_pandas(self, frames: list[pd.DataFrame]) -> List[StoryArc]:
        arcs: list[StoryArc] = []
        for frame in frames:
            if "Arc" not in frame.columns:
                continue
            for _, row in frame.iterrows():
                arcs.append(
                    StoryArc(
                        name=str(row.get("Arc", "")).strip(),
                        start_episode=None,
                        end_episode=None,
                        synopsis=str(row.get("Summary", "")).strip()[:200],
                        is_filler="Filler" in str(row.get("Type", "")),
                    )
                )
        logger.info("Parsed %d arcs via pandas", len(arcs))
        return arcs

    def _parse_manually(self, html: str) -> List[StoryArc]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        arcs: list[StoryArc] = []
        if not table:
            logger.warning("Story arc table not found on Fandom page")
            return arcs
        for row in table.find_all("tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) < 2:
                continue
            name = cols[0].text.strip()
            synopsis = cols[1].text.strip()[:200]
            arcs.append(StoryArc(name=name, start_episode=None, end_episode=None, synopsis=synopsis))
        logger.info("Parsed %d arcs via manual parser", len(arcs))
        return arcs
