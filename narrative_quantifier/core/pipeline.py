from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from narrative_quantifier.cleaner.text_normalizer import CleanResult, normalize_text
from narrative_quantifier.core.config import ModelRoutingPreference, PipelineConfig
from narrative_quantifier.db.models import RoutingDecision, SceneRecord, SceneVector
from narrative_quantifier.engines.metrics_engine import (
    build_scene_vector,
    dta_ratio,
    emotional_volatility,
    tempo_metrics,
)
from narrative_quantifier.engines.power_engine import evaluate_power
from narrative_quantifier.engines.quality_engine import quality_score
from narrative_quantifier.engines.theme_engine import classify_state
from narrative_quantifier.harvester.file_ingestor import FileIngestor
from narrative_quantifier.pattern_miner.pattern_miner import PatternSummary, mine_patterns
from narrative_quantifier.scene_cutter.rules import Scene, segment_text


class NarrativePipeline:
    """End-to-end orchestrator for the TSUKI-NO-ME v3 reference implementation."""

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()
        self.ingestor = FileIngestor()

    # API -----------------------------------------------------
    def run_file(self, path: Path, work_id: str, chapter_id: Optional[str] = None) -> List[SceneRecord]:
        harvested = self.ingestor.ingest(path)
        cleaned = normalize_text(harvested.text)
        return self.run_text(cleaned, work_id=work_id, chapter_id=chapter_id)

    def run_text(self, clean_result: CleanResult, work_id: str, chapter_id: Optional[str] = None) -> List[SceneRecord]:
        scenes = segment_text(clean_result.text, max_scene_chars=self.config.max_scene_chars)
        return self._process_scenes(scenes, work_id=work_id, chapter_id=chapter_id)

    # Internals ------------------------------------------------
    def _process_scenes(
        self, scenes: Iterable[Scene], work_id: str, chapter_id: Optional[str]
    ) -> List[SceneRecord]:
        records: List[SceneRecord] = []
        history_tokens: List[List[str]] = []
        power_history: List[float] = []
        sentiments: List[float] = []

        for scene in scenes:
            previous_text = records[-1].text if records else None
            vector = build_scene_vector(
                text=scene.text,
                previous_text=previous_text,
                history_tokens=history_tokens,
                novelty_window=self.config.novelty_window,
            )
            sentiments.append(vector.S_t)
            tempo = tempo_metrics(scene.text)
            power = evaluate_power(scene.text, power_history, sigma=self.config.power_creep_sigma)
            power_history.append(power.feat_magnitude)
            scene_dta = dta_ratio(scene.text)
            volatility = emotional_volatility(sentiments)
            state = classify_state(vector.S_t, tempo.tempo_shift, power.feat_magnitude)
            score = quality_score(vector, self.config.quality_weights)

            anomalies = []
            if power.creep_sigma >= self.config.power_creep_sigma:
                anomalies.append("power_creep")
            if scene_dta > 0.85:
                anomalies.append("dialogue_heavy")
            if score < 35:
                anomalies.append("low_quality")

            record = SceneRecord(
                work_id=work_id,
                chapter_id=chapter_id,
                scene_id=f"{chapter_id or 'work'}-{scene.index:03d}",
                offsets={"start_char": scene.start, "end_char": scene.end},
                text=scene.text,
                vector=vector,
                tempo=tempo,
                dta_ratio=scene_dta,
                emotional_volatility=volatility,
                power_creep_sigma=power.creep_sigma,
                markov_state=state,
                quality_score=score,
                anomalies=anomalies,
                provenance={"pipeline_stage": "engines.v1"},
            )
            records.append(record)
            history_tokens.append(scene.text.lower().split())

        return records

    # Persistence / export ------------------------------------
    @staticmethod
    def export_jsonl(records: Iterable[SceneRecord], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(_scene_to_dict(record), ensure_ascii=False) + "\n")

    # Routing stubs -------------------------------------------
    def route_model(self, preference: ModelRoutingPreference) -> RoutingDecision:
        """Simulate Strategy + Circuit Breaker decisions.

        The real system would track latency/errors; here we expose the intent so
        downstream callers can assert routing policy in tests.
        """

        model = preference.preferred_models[0]
        fallback_used = False
        reason = "preferred model available"
        if preference.allow_fallbacks and preference.task_type == "classification":
            model = preference.preferred_models[-1]
            fallback_used = True
            reason = "fallback chosen for latency"
        return RoutingDecision(
            task_type=preference.task_type,
            model_used=model,
            latency_ms=self.config.target_latency_ms,
            confidence=self.config.confidence_needed,
            fallback_used=fallback_used,
            reason=reason,
        )


def _scene_to_dict(record: SceneRecord) -> dict:
    return {
        "work_id": record.work_id,
        "chapter_id": record.chapter_id,
        "scene_id": record.scene_id,
        "offsets": record.offsets,
        "vector": {
            "S_t": record.vector.S_t,
            "L_t": record.vector.L_t,
            "F_t": record.vector.F_t,
            "N_t": record.vector.N_t,
            "I_t": record.vector.I_t,
        },
        "tempo": {
            "wps": record.tempo.wps,
            "tempo_shift": record.tempo.tempo_shift,
        },
        "dta_ratio": record.dta_ratio,
        "emotional_volatility": record.emotional_volatility,
        "power_creep_sigma": record.power_creep_sigma,
        "markov_state": record.markov_state,
        "quality_score": record.quality_score,
        "anomalies": record.anomalies,
        "provenance": record.provenance,
    }


def summarize_patterns(records: Iterable[SceneRecord]) -> PatternSummary:
    return mine_patterns(records)
