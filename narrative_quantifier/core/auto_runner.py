from __future__ import annotations

import json
import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Optional, Sequence

from narrative_quantifier.cleaner.text_normalizer import normalize_text
from narrative_quantifier.core.pipeline import NarrativePipeline, summarize_patterns
from narrative_quantifier.db.models import SceneRecord
from narrative_quantifier.harvester.web_ingestor import WebHarvestResult, WebIngestor
from narrative_quantifier.pattern_miner.pattern_miner import PatternSummary


@dataclass
class CorpusAnalytics:
    total_works: int
    total_scenes: int
    avg_quality: float
    avg_dta: float
    acceptance_index: float
    climax_map: Dict[str, str]
    pacing_alerts: List[str] = field(default_factory=list)


@dataclass
class CorpusReport:
    records: List[SceneRecord]
    patterns: PatternSummary
    analytics: CorpusAnalytics
    graphs: List[Path]


class AutoRunner:
    """Orchestrates multi-obra ingestion (local + web) and reporting."""

    def __init__(self, pipeline: Optional[NarrativePipeline] = None, output_dir: Optional[Path] = None) -> None:
        self.pipeline = pipeline or NarrativePipeline()
        self.web_ingestor = WebIngestor()
        self.output_dir = output_dir or Path("outputs/auto")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        local_root: Optional[Path] = None,
        url_list: Optional[Sequence[str]] = None,
    ) -> CorpusReport:
        records: List[SceneRecord] = []
        graphs: List[Path] = []

        for path in self._discover_local(local_root):
            work_id = path.stem
            chapter_id = path.parent.name if path.parent != (local_root or path.parent) else None
            records.extend(self.pipeline.run_file(path, work_id=work_id, chapter_id=chapter_id))

        for web_item in self._ingest_web(url_list or []):
            clean = normalize_text(web_item.text)
            records.extend(
                self.pipeline.run_text(clean, work_id=web_item.work_id, chapter_id="web")
            )

        patterns = summarize_patterns(records)
        analytics = self._compute_analytics(records)
        graphs.extend(self._generate_graphs(records))

        self._export_json("patterns.json", _pattern_summary_to_dict(patterns))
        self._export_json("analytics.json", analytics.__dict__)

        return CorpusReport(records=records, patterns=patterns, analytics=analytics, graphs=graphs)

    # Discovery -------------------------------------------------------------
    def _discover_local(self, root: Optional[Path]) -> List[Path]:
        if root is None:
            return []
        if not root.exists():
            return []
        candidates = [
            p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md"}
        ]
        return sorted([p for p in candidates if p.name != "seed_urls.txt"])

    def _ingest_web(self, urls: Iterable[str]) -> List[WebHarvestResult]:
        results: List[WebHarvestResult] = []
        for url in urls:
            if not url.strip() or url.strip().startswith("#"):
                continue
            try:
                results.append(self.web_ingestor.ingest(url.strip()))
            except Exception as exc:  # pragma: no cover - resilience path
                print(f"[warn] No se pudo scrapear {url}: {exc}")
        return results

    # Analytics -------------------------------------------------------------
    def _compute_analytics(self, records: Iterable[SceneRecord]) -> CorpusAnalytics:
        records_list = list(records)
        if not records_list:
            return CorpusAnalytics(
                total_works=0,
                total_scenes=0,
                avg_quality=0.0,
                avg_dta=0.0,
                acceptance_index=0.0,
                climax_map={},
                pacing_alerts=[],
            )

        avg_quality = mean(scene.quality_score for scene in records_list)
        avg_dta = mean(scene.dta_ratio for scene in records_list)
        grouped: Dict[str, List[SceneRecord]] = {}
        for scene in records_list:
            grouped.setdefault(scene.work_id, []).append(scene)

        climax_map: Dict[str, str] = {}
        pacing_alerts: List[str] = []
        for work_id, scenes in grouped.items():
            ordered = sorted(scenes, key=lambda s: s.offsets.get("start_char", 0))
            top_scene = max(ordered, key=lambda s: s.quality_score)
            climax_map[work_id] = top_scene.scene_id
            for previous, current in zip(ordered, ordered[1:]):
                if previous.quality_score - current.quality_score > 15:
                    pacing_alerts.append(
                        f"Caída brusca de calidad tras {previous.scene_id} → {current.scene_id}"
                    )

        volatility = pstdev([scene.quality_score for scene in records_list]) if len(records_list) > 1 else 0.0
        acceptance_index = max(0.0, avg_quality - volatility)

        return CorpusAnalytics(
            total_works=len(grouped),
            total_scenes=len(records_list),
            avg_quality=round(avg_quality, 2),
            avg_dta=round(avg_dta, 3),
            acceptance_index=round(acceptance_index, 2),
            climax_map=climax_map,
            pacing_alerts=pacing_alerts,
        )

    # Graphs ----------------------------------------------------------------
    def _require_matplotlib(self):
        spec = importlib.util.find_spec("matplotlib")
        if spec is None:
            print(
                "[warn] matplotlib no está instalado; se omiten las gráficas. Instala con `pip install matplotlib`."
            )
            return None
        import matplotlib.pyplot as plt  # type: ignore

        return plt

    def _generate_graphs(self, records: Iterable[SceneRecord]) -> List[Path]:
        records_list = list(records)
        if not records_list:
            return []

        plt = self._require_matplotlib()
        if plt is None:
            return []
        graphs: List[Path] = []

        grouped: Dict[str, List[SceneRecord]] = {}
        for scene in records_list:
            grouped.setdefault(scene.work_id, []).append(scene)

        # Quality trend per work
        fig, ax = plt.subplots(figsize=(10, 5))
        for work_id, scenes in grouped.items():
            ordered = sorted(scenes, key=lambda s: s.offsets.get("start_char", 0))
            x = list(range(1, len(ordered) + 1))
            y = [s.quality_score for s in ordered]
            ax.plot(x, y, marker="o", label=work_id)
            climax_idx = y.index(max(y))
            ax.axvline(x[climax_idx], color="gray", linestyle="--", alpha=0.4)
        ax.set_title("Curva de calidad por escena")
        ax.set_xlabel("Índice de escena")
        ax.set_ylabel("Quality score")
        ax.legend()
        quality_path = self.output_dir / "quality_trends.png"
        fig.tight_layout()
        fig.savefig(quality_path)
        plt.close(fig)
        graphs.append(quality_path)

        # DTA ratio vs quality scatter
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(
            [s.dta_ratio for s in records_list],
            [s.quality_score for s in records_list],
            alpha=0.6,
        )
        ax.set_title("Relación diálogo/acción (DTA) vs calidad")
        ax.set_xlabel("DTA ratio")
        ax.set_ylabel("Quality score")
        scatter_path = self.output_dir / "dta_vs_quality.png"
        fig.tight_layout()
        fig.savefig(scatter_path)
        plt.close(fig)
        graphs.append(scatter_path)

        return graphs

    # Persistence -----------------------------------------------------------
    def _export_json(self, filename: str, payload: dict) -> None:
        path = self.output_dir / filename
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)


def _pattern_summary_to_dict(summary: PatternSummary) -> dict:
    return {
        "rules": [
            {"description": rule.description, "rationale": rule.rationale}
            for rule in summary.rules
        ],
        "anomalies": summary.anomalies,
    }

