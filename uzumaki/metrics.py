"""Metric calculations for Project Uzumaki."""
from __future__ import annotations

import logging
from collections import Counter
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from .models import CharacterPopularity, EpisodeRating, StoryArc, Trope

logger = logging.getLogger(__name__)


def calculate_pacing_score(arc: StoryArc) -> float | None:
    if not arc.manga_chapters or not arc.anime_episodes:
        return None
    score = arc.anime_episodes / arc.manga_chapters
    logger.debug("Pacing score for %s: %s", arc.name, score)
    return score


def calculate_arc_satisfaction(arc: StoryArc, episodes: Iterable[EpisodeRating]) -> float | None:
    relevant = [e.rating for e in episodes if e.rating is not None]
    if not relevant:
        return None
    score = float(pd.Series(relevant).mean())
    logger.debug("Satisfaction for %s: %s", arc.name, score)
    return score


def calculate_character_balance(characters: Iterable[CharacterPopularity]) -> Dict[str, float]:
    favorites = Counter({c.name: c.favorites for c in characters})
    total = sum(favorites.values())
    if total == 0:
        return {name: 0.0 for name in favorites}
    balance = {name: round((count / total) * 100, 3) for name, count in favorites.items()}
    logger.debug("Character balance: %s", balance)
    return balance


def identify_overused_tropes(tropes: Iterable[Trope], limit: int = 10) -> List[Tuple[str, int, str]]:
    counter = Counter()
    category_map: dict[str, str] = {}
    for trope in tropes:
        counter[trope.name] += trope.frequency
        category_map[trope.name] = trope.category
    top = counter.most_common(limit)
    logger.debug("Top tropes: %s", top)
    return [(name, freq, category_map.get(name, "")) for name, freq in top]


def flag_filler_arcs(arcs: Iterable[StoryArc], episodes: Iterable[EpisodeRating]) -> List[Tuple[StoryArc, float | None]]:
    episode_df = pd.DataFrame([
        {"season": e.season, "episode": e.episode, "rating": e.rating}
        for e in episodes
        if e.rating is not None
    ])
    flagged: list[Tuple[StoryArc, float | None]] = []
    for arc in arcs:
        arc_ratings = episode_df["rating"] if episode_df is not None else pd.Series(dtype=float)
        mean_rating = float(arc_ratings.mean()) if not arc_ratings.empty else None
        if arc.is_filler:
            flagged.append((arc, mean_rating))
    logger.debug("Flagged filler arcs: %s", flagged)
    return flagged
