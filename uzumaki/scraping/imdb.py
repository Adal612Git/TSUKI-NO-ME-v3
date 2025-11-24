"""Scraper for IMDb using Selenium."""
from __future__ import annotations

import logging
import random
import time
from dataclasses import asdict
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from ..models import EpisodeRating

logger = logging.getLogger(__name__)


class IMDBScraper:
    base_url = "https://www.imdb.com/title/tt0988824/episodes"

    def __init__(self, driver: webdriver.Remote | None = None) -> None:
        self._driver = driver or webdriver.Chrome()

    def __enter__(self) -> "IMDBScraper":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        try:
            self._driver.quit()
        except WebDriverException:
            logger.exception("Failed to close WebDriver")

    def fetch_all(self, seasons: range | None = None) -> List[EpisodeRating]:
        seasons = seasons or range(1, 22)
        self._driver.get(self.base_url)
        all_episodes: list[EpisodeRating] = []

        season_select = Select(self._driver.find_element(By.ID, "bySeason"))
        available = {int(option.get_attribute("value")) for option in season_select.options if option.get_attribute("value")}
        target_seasons = [s for s in seasons if s in available]

        for season in target_seasons:
            logger.info("Scraping IMDb season %s", season)
            season_select.select_by_value(str(season))
            time.sleep(random.uniform(2, 5))
            episodes = self._parse_episode_list(season)
            all_episodes.extend(episodes)
        logger.info("Collected %d episode ratings", len(all_episodes))
        return all_episodes

    def _parse_episode_list(self, season: int) -> List[EpisodeRating]:
        episodes: list[EpisodeRating] = []
        episode_items = self._driver.find_elements(By.CSS_SELECTOR, "div.list.detail.eplist > div.list_item")
        if not episode_items:
            logger.warning("No episodes found for season %s", season)
            return episodes

        for idx, item in enumerate(episode_items, start=1):
            try:
                title = item.find_element(By.CSS_SELECTOR, "strong a").text
            except NoSuchElementException:
                title = "Unknown"
            try:
                rating_text = item.find_element(By.CSS_SELECTOR, "span.ipl-rating-star__rating").text
                rating = float(rating_text) if rating_text else None
            except (NoSuchElementException, ValueError):
                rating = None
            try:
                votes_text = item.find_element(By.CSS_SELECTOR, "span.ipl-rating-star__total-votes").text
                votes = int(votes_text.strip("() ").replace(",", ""))
            except (NoSuchElementException, ValueError):
                votes = None
            episodes.append(EpisodeRating(season=season, episode=idx, title=title, rating=rating, votes=votes))
        logger.debug("Season %s episodes: %s", season, [asdict(e) for e in episodes])
        return episodes
