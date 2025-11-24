"""Scraper for TV Tropes trope extraction."""
from __future__ import annotations

import logging
from collections import Counter
from typing import List

from bs4 import BeautifulSoup

from .base import respectful_get
from ..models import Trope

logger = logging.getLogger(__name__)


class TVTropesScraper:
    url = "https://tvtropes.org/pmwiki/pmwiki.php/Anime/Naruto"
    TARGET_SECTIONS = [
        "Main Tropes",
        "Character Tropes",
        "Arc-Specific Tropes",
    ]

    def fetch(self) -> List[Trope]:
        logger.info("Fetching trope list from TV Tropes")
        response = respectful_get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")

        trope_counter: Counter[str] = Counter()
        for section in self.TARGET_SECTIONS:
            header = soup.find(lambda tag: tag.name in {"h2", "h3"} and section in tag.text)
            if not header:
                logger.warning("Section '%s' not found", section)
                continue
            ul = header.find_next("ul")
            if not ul:
                logger.warning("List for section '%s' missing", section)
                continue
            for li in ul.find_all("li"):
                name = li.text.strip()
                if name:
                    trope_counter[(section, name)] += 1

        tropes: list[Trope] = [
            Trope(name=name, category=category, frequency=count)
            for (category, name), count in trope_counter.most_common()
        ]
        logger.info("Collected %d tropes", len(tropes))
        return tropes
