from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


def _default_quality_weights() -> Dict[str, float]:
    return {"S_t": 1.0, "L_t": 0.8, "F_t": 1.2, "N_t": 0.9, "I_t": 1.1}


@dataclass
class PipelineConfig:
    """Configuration for the end-to-end narrative pipeline.

    These defaults are intentionally lightweight to avoid heavyweight dependencies
    while still providing a practical baseline for quantitative analysis.
    """

    max_scene_chars: int = 1200
    target_latency_ms: int = 750
    confidence_needed: float = 0.65
    quality_weights: Dict[str, float] = field(default_factory=_default_quality_weights)
    novelty_window: int = 12
    power_creep_sigma: float = 2.0
    boredom_floor: float = 0.15


@dataclass
class ModelRoutingPreference:
    """Simple hinting for Ollama router selection.

    The real system would incorporate cost/latency history. Here we capture the
    intent so strategy and circuit-breaker logic remain explicit in code.
    """

    task_type: str
    preferred_models: List[str]
    allow_fallbacks: bool = True
