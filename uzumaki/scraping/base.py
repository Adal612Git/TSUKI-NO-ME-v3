"""Base utilities for scrapers."""
from __future__ import annotations

import logging
import random
import time
from typing import Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_random


logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Raised when a scraper cannot recover from an error."""


def respectful_get(url: str, *, headers: dict | None = None, sleep_range: tuple[float, float] = (1.0, 3.0)) -> requests.Response:
    """Perform a GET request with a randomized polite delay and retries."""

    @retry(stop=stop_after_attempt(3), wait=wait_random(*sleep_range))
    def _request() -> requests.Response:
        logger.debug("Requesting %s", url)
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response

    time.sleep(random.uniform(*sleep_range))
    return _request()


def chunked(iterable: Iterable, size: int) -> Iterable[list]:
    """Yield successive chunks from an iterable."""
    chunk: list = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
