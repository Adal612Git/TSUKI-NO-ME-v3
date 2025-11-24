"""Utilities to unify and clean scraped data."""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import asdict
from typing import Iterable

import pandas as pd

from .models import CharacterPopularity, CleanedDataset, EpisodeRating, StoryArc, Trope

logger = logging.getLogger(__name__)


class DataCleaner:
    """Normalize raw scraped artifacts into a unified dataset."""

    def __init__(self) -> None:
        self.dataset = CleanedDataset()

    def add_characters(self, characters: Iterable[CharacterPopularity]) -> None:
        uniques: dict[str, CharacterPopularity] = {c.name: c for c in characters}
        self.dataset.characters = list(uniques.values())
        logger.debug("Characters normalized: %s", [asdict(c) for c in self.dataset.characters])

    def add_episodes(self, episodes: Iterable[EpisodeRating]) -> None:
        seen = {(e.season, e.episode) for e in self.dataset.episodes}
        for episode in episodes:
            if (episode.season, episode.episode) not in seen:
                self.dataset.episodes.append(episode)
        self.dataset.episodes.sort(key=lambda e: (e.season, e.episode))
        logger.debug("Episodes normalized: %s", [asdict(e) for e in self.dataset.episodes])

    def add_arcs(self, arcs: Iterable[StoryArc]) -> None:
        self.dataset.arcs = list({a.name: a for a in arcs}.values())
        logger.debug("Arcs normalized: %s", [asdict(a) for a in self.dataset.arcs])

    def add_tropes(self, tropes: Iterable[Trope]) -> None:
        self.dataset.tropes = list({(t.category, t.name): t for t in tropes}.values())
        logger.debug("Tropes normalized: %s", [asdict(t) for t in self.dataset.tropes])

    def to_sqlite(self, path: str) -> None:
        logger.info("Persisting cleaned dataset to %s", path)
        conn = sqlite3.connect(path)
        try:
            self._persist_with_conn(conn)
        finally:
            conn.close()

    def snapshot_to_excel(self, path: str) -> None:
        logger.info("Persisting cleaned dataset snapshot to %s", path)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            pd.DataFrame([asdict(e) for e in self.dataset.episodes]).to_excel(writer, sheet_name="episodes", index=False)
            pd.DataFrame([asdict(c) for c in self.dataset.characters]).to_excel(writer, sheet_name="characters", index=False)
            pd.DataFrame([asdict(a) for a in self.dataset.arcs]).to_excel(writer, sheet_name="arcs", index=False)
            pd.DataFrame([asdict(t) for t in self.dataset.tropes]).to_excel(writer, sheet_name="tropes", index=False)

    def _persist_with_conn(self, conn: sqlite3.Connection) -> None:
        pd.DataFrame([asdict(e) for e in self.dataset.episodes]).to_sql("episodes", conn, if_exists="replace", index=False)
        pd.DataFrame([asdict(c) for c in self.dataset.characters]).to_sql("characters", conn, if_exists="replace", index=False)
        pd.DataFrame([asdict(a) for a in self.dataset.arcs]).to_sql("arcs", conn, if_exists="replace", index=False)
        pd.DataFrame([asdict(t) for t in self.dataset.tropes]).to_sql("tropes", conn, if_exists="replace", index=False)
