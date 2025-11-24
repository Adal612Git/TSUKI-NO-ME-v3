"""Base utilities for scrapers."""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Iterable

import httpx
import requests
from tenacity import retry, stop_after_attempt, wait_random


logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Raised when a scraper cannot recover from an error."""


@dataclass
class CacheEntry:
    url: str
    etag: str | None
    last_modified: str | None
    content: bytes
    status_code: int


class AsyncCachedClient:
    """Lightweight async HTTP client with ETag/Last-Modified caching."""

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        headers: dict[str, str] | None = None,
        cookies: httpx.Cookies | dict[str, str] | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers, cookies=cookies)
        self._cache: dict[str, CacheEntry] = {}

    async def __aenter__(self) -> "AsyncCachedClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self._client.aclose()

    async def get(self, url: str, **kwargs) -> httpx.Response:
        conditional_headers: dict[str, str] = {}
        if cached := self._cache.get(url):
            if cached.etag:
                conditional_headers["If-None-Match"] = cached.etag
            if cached.last_modified:
                conditional_headers["If-Modified-Since"] = cached.last_modified
        headers = kwargs.pop("headers", {}) or {}
        headers.update(conditional_headers)
        response = await self._client.get(url, headers=headers, **kwargs)
        if response.status_code == 304 and cached:
            logger.debug("Cache hit for %s", url)
            return self._build_cached_response(response, cached)
        if response.status_code < 400:
            self._cache[url] = CacheEntry(
                url=url,
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                content=response.content,
                status_code=response.status_code,
            )
        return response

    def _build_cached_response(self, response: httpx.Response, cache: CacheEntry) -> httpx.Response:
        new_response = httpx.Response(
            status_code=cache.status_code,
            headers=response.headers,
            content=cache.content,
            request=response.request,
        )
        return new_response


class BaseAsyncScraper:
    name: str = "scraper"

    def __init__(self, *, client: AsyncCachedClient | None = None) -> None:
        self.client = client or AsyncCachedClient()

    async def __aenter__(self) -> "BaseAsyncScraper":
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.client.__aexit__(exc_type, exc, tb)


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


def run_in_executor(func, *args, loop: asyncio.AbstractEventLoop | None = None):
    """Run blocking scraper logic in a thread without blocking the event loop."""

    loop = loop or asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args)
