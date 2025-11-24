"""SQLite persistence with schema safeguards."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from uzumaki.cleaning import ensure_columns, warn_if_empty

logger = logging.getLogger(__name__)


class SQLiteWriter:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True, parents=True)

    def write_table(self, rows: Iterable[dict], name: str, columns: Sequence[str] | None = None) -> None:
        df = warn_if_empty(name, rows)
        if df.empty or len(df.columns) == 0:
            return
        if columns:
            df = ensure_columns(df, columns)
        with sqlite3.connect(self.path) as conn:
            df.to_sql(name, conn, if_exists="replace", index=False)
            logger.info("Persisted %d rows to table %s", len(df), name)

    def write_dataset(self, tables: dict[str, tuple[Iterable[dict], Sequence[str] | None]]) -> None:
        for name, (rows, columns) in tables.items():
            self.write_table(rows, name, columns)
