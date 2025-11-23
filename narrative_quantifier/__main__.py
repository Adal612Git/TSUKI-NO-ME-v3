from __future__ import annotations

import argparse
from pathlib import Path

from narrative_quantifier.cleaner.text_normalizer import normalize_text
from narrative_quantifier.core.pipeline import NarrativePipeline, summarize_patterns


def main() -> None:
    parser = argparse.ArgumentParser(description="TSUKI-NO-ME v3 narrative quantifier")
    parser.add_argument("source", type=Path, help="Ruta de archivo .txt/.md a analizar")
    parser.add_argument("--work-id", default="work", help="Identificador de la obra")
    parser.add_argument("--chapter-id", default=None, help="Identificador del capítulo")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/scenes.jsonl"),
        help="Ruta de exportación JSONL",
    )
    args = parser.parse_args()

    pipeline = NarrativePipeline()
    harvested_text = args.source.read_text(encoding="utf-8")
    clean_result = normalize_text(harvested_text)
    records = pipeline.run_text(clean_result, work_id=args.work_id, chapter_id=args.chapter_id)
    pipeline.export_jsonl(records, args.output)
    summary = summarize_patterns(records)

    print(f"Procesadas {len(records)} escenas → {args.output}")
    print("Reglas sugeridas:")
    for rule in summary.rules:
        print(f"- {rule.description} ({rule.rationale})")
    if summary.anomalies:
        print("Anomalías detectadas:")
        for issue in summary.anomalies:
            print(f"- {issue}")


if __name__ == "__main__":
    main()
