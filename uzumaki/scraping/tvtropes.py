"""Scraper for TV Tropes trope extraction."""
from __future__ import annotations

import logging
import random
from collections import Counter
from typing import List

import cloudscraper
import requests
from bs4 import BeautifulSoup

from ..models import Trope

logger = logging.getLogger(__name__)


class TVTropesScraper:
    url = "https://tvtropes.org/pmwiki/pmwiki.php/Anime/Naruto"
    FALLBACK_URLS = [
        url,
        "https://tvtropes.org/pmwiki/pmwiki.php/Main/Naruto",
        "https://tvtropes.org/pmwiki/pmwiki.php/Anime/NarutoShippuden",
    ]
    TARGET_SECTIONS = [
        "Main Tropes",
        "Character Tropes",
        "Arc-Specific Tropes",
    ]
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.142 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/125.0.2535.79",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.4166.129 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    ]

    def _build_headers(self, user_agent: str) -> dict[str, str]:
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Sec-CH-UA": '"Chromium";v="125", "Not.A/Brand";v="24", "Google Chrome";v="125"',
            "Sec-CH-UA-Platform": '"Windows"',
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }

    def _request_page(self, url: str) -> tuple[requests.Response | None, bool]:
        user_agent = random.choice(self.USER_AGENTS)
        headers = self._build_headers(user_agent)
        scraper = cloudscraper.create_scraper()
        logger.debug("Requesting %s with rotated User-Agent", url)

        try:
            response = scraper.get(url, headers=headers, timeout=20)
        except requests.RequestException as exc:
            logger.warning("TV Tropes request failed for %s: %s", url, exc)
            return None, False

        if response.status_code == 403:
            logger.warning("TV Tropes blocked the request with 403 Forbidden for %s", url)
            return None, True
        if response.status_code >= 400:
            logger.warning(
                "TV Tropes returned status %s for %s", response.status_code, url
            )
            return None, False

        return response, False

    def fetch(self) -> List[Trope]:
        logger.info("Fetching trope list from TV Tropes")
        response: requests.Response | None = None
        blocked = False
        for candidate_url in self.FALLBACK_URLS:
            response, blocked = self._request_page(candidate_url)
            if blocked:
                logger.warning("TV Tropes access blocked; returning no tropes")
                return []
            if response:
                logger.info("TV Tropes content fetched from %s", candidate_url)
                break

        if response is None:
            logger.warning("TV Tropes scraping failed; continuing pipeline without tropes")
            return []

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
