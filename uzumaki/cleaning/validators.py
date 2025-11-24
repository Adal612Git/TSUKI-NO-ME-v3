"""Validation helpers for cleaned datasets."""
from __future__ import annotations

import logging
from typing import Iterable, Sequence

import pandas as pd

logger = logging.getLogger(__name__)


def ensure_columns(df: pd.DataFrame, required: Sequence[str]) -> pd.DataFrame:
    """Add any missing columns to the dataframe to satisfy a target schema.

    The function does not drop extra columns to preserve future compatibility,
    but guarantees the presence of the requested names.
    """

    for column in required:
        if column not in df.columns:
            df[column] = None
    return df


def warn_if_empty(table: str, rows: Iterable[dict]) -> pd.DataFrame:
    """Build a dataframe from rows and log if it is empty."""

    df = pd.DataFrame(list(rows))
    if df.empty:
        logger.warning("No rows provided for %s; downstream writes will be skipped", table)
    return df
