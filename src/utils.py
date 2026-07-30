"""Reusable validation, scoring and export functions."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import matplotlib.figure
import pandas as pd


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Raise a clear error when an input table is missing required columns."""
    missing = sorted(set(required_columns) - set(dataframe.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def inverse_percentile_score(series: pd.Series) -> pd.Series:
    """Return a 0-100 score where lower observed values receive higher scores."""
    numeric = pd.to_numeric(series, errors="raise")
    ranks = numeric.rank(method="average")
    rank_range = ranks.max() - ranks.min()
    if rank_range == 0:
        return pd.Series(50.0, index=series.index, dtype="float64")
    return ((ranks.max() - ranks) / rank_range * 100).round(2)


def save_figure(
    figure: matplotlib.figure.Figure,
    output_path: Path,
    *,
    dpi: int = 150,
) -> None:
    """Create the output directory and save a publication-ready figure."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
