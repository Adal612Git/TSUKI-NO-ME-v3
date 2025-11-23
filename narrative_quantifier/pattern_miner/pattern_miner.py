from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from narrative_quantifier.db.models import SceneRecord


@dataclass
class Rule:
    description: str
    rationale: str


@dataclass
class PatternSummary:
    rules: List[Rule]
    anomalies: List[str]


def mine_patterns(scenes: Iterable[SceneRecord]) -> PatternSummary:
    scenes_list = list(scenes)
    if not scenes_list:
        return PatternSummary(rules=[], anomalies=[])

    avg_dta = sum(scene.dta_ratio for scene in scenes_list) / len(scenes_list)
    avg_quality = sum(scene.quality_score for scene in scenes_list) / len(scenes_list)
    dta_rule = Rule(
        description=f"Mantener DTA ratio cercano a {avg_dta:.2f}",
        rationale="Equilibrio diálogo/acción derivado del corpus actual.",
    )

    anomalies: List[str] = []
    for scene in scenes_list:
        if scene.power_creep_sigma >= 2.0:
            anomalies.append(f"Power creep en {scene.scene_id} (σ={scene.power_creep_sigma:.2f})")
        if scene.quality_score < avg_quality * 0.6:
            anomalies.append(f"Escena de baja calidad: {scene.scene_id} (score {scene.quality_score:.1f})")

    rules = [dta_rule]
    if avg_quality > 60:
        rules.append(
            Rule(
                description="Replicar curva de calidad observada",
                rationale="El corpus mantiene nivel alto; usar como baseline de ritmo y emoción.",
            )
        )

    return PatternSummary(rules=rules, anomalies=anomalies)
