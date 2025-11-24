"""Excel snapshot writer that tolerates empty datasets."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

from uzumaki.cleaning import warn_if_empty

logger = logging.getLogger(__name__)


class ExcelSnapshot:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True, parents=True)

    def write_tab(self, rows: Iterable[dict], sheet_name: str, writer: pd.ExcelWriter) -> None:
        df = warn_if_empty(sheet_name, rows)
        if df.empty or len(df.columns) == 0:
            return
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info("Persisted %d rows to sheet %s", len(df), sheet_name)

    def write_workbook(self, tabs: dict[str, Iterable[dict]]) -> None:
        with pd.ExcelWriter(self.path, engine="openpyxl") as writer:
            for name, rows in tabs.items():
                self.write_tab(rows, name, writer)
