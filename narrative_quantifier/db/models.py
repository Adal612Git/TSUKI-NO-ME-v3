from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SceneVector:
    S_t: float
    L_t: float
    F_t: float
    N_t: float
    I_t: float


@dataclass
class TempoMetrics:
    wps: float
    tempo_shift: float


@dataclass
class SceneRecord:
    work_id: str
    chapter_id: Optional[str]
    scene_id: str
    offsets: Dict[str, int]
    text: str
    vector: SceneVector
    tempo: TempoMetrics
    dta_ratio: float
    emotional_volatility: float
    power_creep_sigma: float
    markov_state: str
    quality_score: float
    anomalies: List[str] = field(default_factory=list)
    provenance: Dict[str, str] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    task_type: str
    model_used: str
    latency_ms: float
    confidence: float
    fallback_used: bool
    reason: str
