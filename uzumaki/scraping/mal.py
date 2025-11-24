"""Scraper for MyAnimeList data."""
from __future__ import annotations

import logging
import random
import time
from typing import List

from bs4 import BeautifulSoup

from .base import respectful_get
from ..models import CharacterPopularity

logger = logging.getLogger(__name__)


class MALScraper:
    stats_url = "https://myanimelist.net/anime/1735/Naruto__Shippuuden/stats"
    characters_url = "https://myanimelist.net/anime/1735/Naruto__Shippuuden/characters"

    def fetch_characters(self) -> List[CharacterPopularity]:
        """Scrape MAL character popularity table."""
        logger.info("Fetching MAL character popularity list")
        response = respectful_get(self.characters_url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="js-anime-character-table")
        characters: list[CharacterPopularity] = []

        if not table:
            logger.warning("Character table not found on MAL page")
            return characters

        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            name_tag = cols[1].find("a")
            favorites_tag = cols[2].find("span") or cols[2]
            if not name_tag or not favorites_tag:
                continue
            name = name_tag.text.strip()
            url = name_tag.get("href", "")
            try:
                favorites = int(favorites_tag.text.replace(",", "").strip())
            except ValueError:
                favorites = 0
            characters.append(CharacterPopularity(name=name, profile_url=url, favorites=favorites))
        logger.info("Collected %d characters from MAL", len(characters))
        return characters

    def fetch_stats(self) -> dict:
        """Scrape MAL statistics page for aggregate information."""
        logger.info("Fetching MAL statistics page")
        response = respectful_get(self.stats_url)
        soup = BeautifulSoup(response.text, "html.parser")
        stats: dict[str, float | int] = {}
        for row in soup.select("div.anime-detail-header-stats div.stat-score div.score-label"):
            label = row.text.strip().lower().replace(" ", "_")
            value_tag = row.find_next("span", class_="score")
            if value_tag:
                try:
                    stats[label] = float(value_tag.text.strip())
                except ValueError:
                    continue
        for row in soup.select("div.anime-detail-header-stats div.stacked div.stat tr"):
            cols = row.find_all("td")
            if len(cols) != 2:
                continue
            label = cols[0].text.strip().lower().replace(" ", "_")
            try:
                value = int(cols[1].text.replace(",", "").strip())
            except ValueError:
                continue
            stats[label] = value
        logger.debug("Stats scraped: %s", stats)
        return stats

    def dump_checkpoint(self, characters: List[CharacterPopularity], path: str) -> None:
        logger.info("Saving MAL checkpoint to %s", path)
        time.sleep(random.uniform(0.2, 0.6))
        with open(path, "w", encoding="utf-8") as fp:
            for character in characters:
                fp.write(f"{character.name}\t{character.favorites}\t{character.profile_url}\n")
