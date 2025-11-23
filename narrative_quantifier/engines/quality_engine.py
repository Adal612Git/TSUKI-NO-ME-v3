from __future__ import annotations

import math
from typing import Dict

from narrative_quantifier.db.models import SceneVector


def quality_score(vector: SceneVector, weights: Dict[str, float]) -> float:
    logits = (
        vector.S_t * weights.get("S_t", 1.0)
        + vector.L_t * weights.get("L_t", 1.0)
        + vector.F_t * weights.get("F_t", 1.0)
        + vector.N_t * weights.get("N_t", 1.0)
        + vector.I_t * weights.get("I_t", 1.0)
    )
    return _sigmoid(logits) * 100


def _sigmoid(x: float) -> float:
    try:
        return 1 / (1 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0
