"""Utilities to unify and clean scraped data."""
from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from .cleaning import deduplicate_by, ensure_columns
from .models import CharacterPopularity, CleanedDataset, EpisodeRating, StoryArc, Trope
from .storage import ExcelSnapshot, SQLiteWriter

logger = logging.getLogger(__name__)


class DataCleaner:
    """Normalize raw scraped artifacts into a unified dataset."""

    def __init__(self) -> None:
        self.dataset = CleanedDataset()

    def add_characters(self, characters: Iterable[CharacterPopularity]) -> None:
        uniques = deduplicate_by(characters, lambda c: c.name.lower())
        self.dataset.characters = uniques
        logger.debug("Characters normalized: %s", [asdict(c) for c in self.dataset.characters])

    def add_episodes(self, episodes: Iterable[EpisodeRating]) -> None:
        uniques = deduplicate_by(episodes, lambda e: (e.season, e.episode))
        self.dataset.episodes = sorted(uniques, key=lambda e: (e.season, e.episode))
        logger.debug("Episodes normalized: %s", [asdict(e) for e in self.dataset.episodes])

    def add_arcs(self, arcs: Iterable[StoryArc]) -> None:
        self.dataset.arcs = deduplicate_by(arcs, lambda a: a.name.lower())
        logger.debug("Arcs normalized: %s", [asdict(a) for a in self.dataset.arcs])

    def add_tropes(self, tropes: Iterable[Trope]) -> None:
        self.dataset.tropes = deduplicate_by(tropes, lambda t: (t.category.lower(), t.name.lower()))
        logger.debug("Tropes normalized: %s", [asdict(t) for t in self.dataset.tropes])

    def to_sqlite(self, path: str) -> None:
        logger.info("Persisting cleaned dataset to %s", path)
        writer = SQLiteWriter(path)
        tables = {
            "episodes": ([asdict(e) for e in self.dataset.episodes], EpisodeRating.__dataclass_fields__.keys()),
            "characters": ([asdict(c) for c in self.dataset.characters], CharacterPopularity.__dataclass_fields__.keys()),
            "arcs": ([asdict(a) for a in self.dataset.arcs], StoryArc.__dataclass_fields__.keys()),
            "tropes": ([asdict(t) for t in self.dataset.tropes], Trope.__dataclass_fields__.keys()),
        }
        writer.write_dataset({name: (rows, list(columns)) for name, (rows, columns) in tables.items()})

    def snapshot_to_excel(self, path: str) -> None:
        logger.info("Persisting cleaned dataset snapshot to %s", path)
        snapshot = ExcelSnapshot(path)
        snapshot.write_workbook(
            {
                "episodes": [asdict(e) for e in self.dataset.episodes],
                "characters": [asdict(c) for c in self.dataset.characters],
                "arcs": [asdict(a) for a in self.dataset.arcs],
                "tropes": [asdict(t) for t in self.dataset.tropes],
            }
        )

    def snapshot_to_parquet(self, directory: str) -> None:
        base = Path(directory)
        base.mkdir(exist_ok=True, parents=True)
        datasets = {
            "episodes": [asdict(e) for e in self.dataset.episodes],
            "characters": [asdict(c) for c in self.dataset.characters],
            "arcs": [asdict(a) for a in self.dataset.arcs],
            "tropes": [asdict(t) for t in self.dataset.tropes],
        }
        for name, rows in datasets.items():
            df = pd.DataFrame(rows)
            if df.empty:
                logger.warning("Skipping %s.parquet — no rows to persist", name)
                continue
            expected = self._expected_columns(name)
            df = ensure_columns(df, expected)
            path = base / f"{name}.parquet"
            df.to_parquet(path, index=False)
            logger.info("Persisted %d rows to %s", len(df), path)

    def _expected_columns(self, name: str) -> list[str]:
        mapping = {
            "episodes": list(EpisodeRating.__dataclass_fields__.keys()),
            "characters": list(CharacterPopularity.__dataclass_fields__.keys()),
            "arcs": list(StoryArc.__dataclass_fields__.keys()),
            "tropes": list(Trope.__dataclass_fields__.keys()),
        }
        return mapping.get(name, [])
