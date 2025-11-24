"""Scraper for Naruto Fandom Wiki story arcs."""
from __future__ import annotations

import logging
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..models import StoryArc

logger = logging.getLogger(__name__)


FANDOM_URLS = [
    "https://naruto.fandom.com/wiki/Story_Arcs",
    "https://naruto.fandom.com/wiki/Category:Story_Arcs",
    "https://naruto.fandom.com/es/wiki/Arcos_Argumentales",
]


class FandomScraper:

    def fetch(self) -> List[StoryArc]:
        logger.info("Fetching story arcs from Fandom")

        for url in FANDOM_URLS:
            logger.debug("Requesting %s", url)
            try:
                response = requests.get(url, timeout=20)
                if response.status_code == 404:
                    logger.warning("Fandom URL %s returned 404; skipping without retry", url)
                    continue
                response.raise_for_status()
            except requests.HTTPError as exc:
                logger.warning("HTTP error fetching %s: %s", url, exc)
                continue
            except requests.RequestException as exc:
                logger.warning("Request error fetching %s: %s", url, exc)
                continue

            try:
                frames = pd.read_html(response.text)
            except (ValueError, ImportError):
                frames = []

            if frames:
                return self._parse_with_pandas(frames)
            return self._parse_manually(response.text)

        logger.warning("All Fandom URLs failed; returning empty story arc list")
        return []

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
