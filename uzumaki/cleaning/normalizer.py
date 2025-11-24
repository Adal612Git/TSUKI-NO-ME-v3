"""Normalization utilities shared across scrapers."""
from __future__ import annotations

import html
import re
from typing import Iterable, TypeVar

T = TypeVar("T")


def normalize_whitespace(text: str | None) -> str:
    if text is None:
        return ""
    cleaned = html.unescape(text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def deduplicate_by(items: Iterable[T], key_func) -> list[T]:
    seen: set[object] = set()
    unique: list[T] = []
    for item in items:
        key = key_func(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
