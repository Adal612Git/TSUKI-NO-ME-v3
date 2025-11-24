"""Scraper for IMDb using Selenium."""
from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import asdict
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ..models import EpisodeRating

logger = logging.getLogger(__name__)


class IMDBScraper:
    base_url = "https://www.imdb.com/title/tt0988824/episodes"

    def __init__(self, driver: webdriver.Remote | None = None) -> None:
        if driver:
            self._driver = driver
        else:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self._driver = webdriver.Chrome(options=options)

    def __enter__(self) -> "IMDBScraper":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        try:
            self._driver.quit()
        except WebDriverException:
            logger.exception("Failed to close WebDriver")

    def fetch_all(self, seasons: range | None = None) -> List[EpisodeRating]:
        seasons = seasons or range(1, 22)
        wait = WebDriverWait(self._driver, 15)
        self._driver.get(self.base_url)
        all_episodes: list[EpisodeRating] = []

        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            logger.warning("IMDb page did not load; skipping IMDb scrape")
            return all_episodes

        season_control = self._find_season_control(wait)
        if season_control is None:
            logger.warning("IMDb season menu not found; skipping IMDb scrape")
            return all_episodes

        if season_control.tag_name.lower() == "select":
            season_select = Select(season_control)
            available = {
                int(option.get_attribute("value"))
                for option in season_select.options
                if option.get_attribute("value")
            }
            target_seasons = [s for s in seasons if s in available]
            for season in target_seasons:
                logger.info("Scraping IMDb season %s", season)
                success = self._load_season_via_select(wait, season_select, season)
                if not success:
                    continue
                episodes = self._parse_episode_list(season)
                all_episodes.extend(episodes)
        else:
            target_seasons = list(seasons)
            for season in target_seasons:
                logger.info("Scraping IMDb season %s via navigation fallback", season)
                success = self._load_season_via_navigation(wait, season)
                if not success:
                    continue
                episodes = self._parse_episode_list(season)
                all_episodes.extend(episodes)

        logger.info("Collected %d episode ratings", len(all_episodes))
        return all_episodes

    def _find_season_control(self, wait: WebDriverWait):
        selectors = [
            (By.XPATH, "//*[@data-testid='episodes-dropdown-trigger']"),
            (By.XPATH, "//select[contains(@class, 'ipc-simple-select__input')]"),
            (By.XPATH, "//button[contains(text(), 'Season') or contains(., 'Season')]"),
        ]
        for by, value in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((by, value)))
                return element
            except TimeoutException:
                continue
        return None

    def _load_season_via_select(self, wait: WebDriverWait, season_select: Select, season: int) -> bool:
        for attempt in range(3):
            try:
                season_select.select_by_value(str(season))
            except NoSuchElementException:
                logger.warning("Season %s not found in IMDb dropdown", season)
                return False
            time.sleep(random.uniform(1, 3))
            if self._wait_for_episode_section(wait):
                return True
        logger.warning("Retries exhausted while loading IMDb season %s", season)
        return False

    def _load_season_via_navigation(self, wait: WebDriverWait, season: int) -> bool:
        for attempt in range(3):
            self._driver.get(f"{self.base_url}?season={season}")
            if self._wait_for_episode_section(wait):
                return True
            time.sleep(1)
        logger.warning("Retries exhausted while loading IMDb season %s via navigation", season)
        return False

    def _wait_for_episode_section(self, wait: WebDriverWait) -> bool:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//section[@data-testid='episodes']")))
            return True
        except TimeoutException:
            return False

    def _parse_episode_list(self, season: int) -> List[EpisodeRating]:
        episodes: list[EpisodeRating] = []
        try:
            container = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//section[@data-testid='episodes']"))
            )
        except TimeoutException:
            logger.warning("No episode section available for season %s", season)
            return episodes

        episode_links = container.find_elements(By.XPATH, ".//a[contains(@href, '/title/') and normalize-space()]")
        if not episode_links:
            logger.warning("No episodes found for season %s", season)
            return episodes

        seen_links: set[str] = set()
        episode_number = 1
        for link in episode_links:
            href = link.get_attribute("href") or ""
            if href in seen_links:
                continue
            seen_links.add(href)
            title = link.text.strip() or "Unknown"
            article = link.find_elements(By.XPATH, "ancestor::article[1]")
            rating, votes = (None, None)
            if not article:
                continue
            rating, votes = self._extract_rating_votes(article[0])
            episodes.append(
                EpisodeRating(
                    season=season,
                    episode=episode_number,
                    title=title,
                    rating=rating,
                    votes=votes,
                )
            )
            episode_number += 1
        logger.debug("Season %s episodes: %s", season, [asdict(e) for e in episodes])
        return episodes

    def _extract_rating_votes(self, article) -> tuple[float | None, int | None]:
        rating = None
        votes = None
        rating_candidates = article.find_elements(
            By.XPATH,
            ".//span[@data-testid='ratingGroup--imdb-rating']//span[normalize-space()]",
        )
        for candidate in rating_candidates:
            match = re.search(r"(\d+(?:\.\d+)?)", candidate.text)
            if match:
                try:
                    rating = float(match.group(1))
                    break
                except ValueError:
                    rating = None
        if rating is None:
            fallback_rating = article.find_elements(By.XPATH, ".//span[contains(@class, 'ipl-rating-star__rating')]")
            if fallback_rating:
                try:
                    rating = float(fallback_rating[0].text)
                except ValueError:
                    rating = None

        vote_elements = article.find_elements(By.XPATH, ".//span[contains(@class, 'total-votes') or contains(text(), 'votes') or contains(text(), '(')]")
        for vote_el in vote_elements:
            digits = re.search(r"([\d,]+)", vote_el.text)
            if digits:
                try:
                    votes = int(digits.group(1).replace(",", ""))
                    break
                except ValueError:
                    votes = None
        return rating, votes
