from __future__ import annotations

from typing import List

from narrative_quantifier.engines.metrics_engine import sentiment_score

STATE_SEQUENCE = ["setup", "tensión", "clímax", "valle"]


def classify_state(sentiment: float, tempo_shift: float, feat_magnitude: float) -> str:
    if feat_magnitude > 1.2 or tempo_shift > 0.5:
        return "clímax"
    if sentiment < -0.1 and tempo_shift < -0.2:
        return "valle"
    if tempo_shift > 0.1:
        return "tensión"
    return "setup"


def suggest_topics(scene_text: str) -> List[str]:
    tokens = {t for t in scene_text.lower().split() if len(t) > 6}
    return sorted(tokens)[:5]
