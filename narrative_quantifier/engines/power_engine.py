from __future__ import annotations

from dataclasses import dataclass
from typing import List

from narrative_quantifier.engines.metrics_engine import _feat_magnitude, _tokenize


@dataclass
class PowerResult:
    feat_magnitude: float
    creep_sigma: float


def evaluate_power(scene_text: str, history: List[float], sigma: float) -> PowerResult:
    magnitude = _feat_magnitude(scene_text)
    if not history:
        return PowerResult(feat_magnitude=magnitude, creep_sigma=0.0)
    avg = sum(history) / len(history)
    variance = sum((h - avg) ** 2 for h in history) / max(1, len(history) - 1)
    std = variance ** 0.5
    if std == 0:
        creep = 0.0
    else:
        creep = abs(magnitude - avg) / std
    return PowerResult(feat_magnitude=magnitude, creep_sigma=creep)
