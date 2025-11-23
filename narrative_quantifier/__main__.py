from __future__ import annotations

import argparse
from pathlib import Path

from narrative_quantifier.cleaner.text_normalizer import normalize_text
from narrative_quantifier.core.auto_runner import AutoRunner
from narrative_quantifier.core.pipeline import NarrativePipeline, summarize_patterns


def main() -> None:
    parser = argparse.ArgumentParser(description="TSUKI-NO-ME v3 narrative quantifier")
    parser.add_argument("source", type=Path, nargs="?", help="Ruta de archivo .txt/.md a analizar")
    parser.add_argument("--work-id", default="work", help="Identificador de la obra")
    parser.add_argument("--chapter-id", default=None, help="Identificador del capítulo")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/scenes.jsonl"),
        help="Ruta de exportación JSONL",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Procesa automáticamente obras locales y URLs definidas en un archivo",
    )
    parser.add_argument(
        "--local-root",
        type=Path,
        default=Path("examples"),
        help="Directorio raíz con obras locales (.txt/.md)",
    )
    parser.add_argument(
        "--url-file",
        type=Path,
        default=Path("examples/seed_urls.txt"),
        help="Archivo de texto con URLs a scrapear (opcional)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/auto"),
        help="Directorio base para exportar datasets y gráficas del modo automático",
    )
    args = parser.parse_args()

    if args.auto:
        url_list = []
        if args.url_file.exists():
            url_list = [line.strip() for line in args.url_file.read_text(encoding="utf-8").splitlines()]
        runner = AutoRunner(output_dir=args.output_dir)
        report = runner.run(local_root=args.local_root, url_list=url_list)
        if report.records:
            export_path = args.output_dir / "scenes.jsonl"
            NarrativePipeline.export_jsonl(report.records, export_path)
            print(f"Procesadas {len(report.records)} escenas de {report.analytics.total_works} obras → {export_path}")
            print(f"Curvas y correlaciones gráficas guardadas en: {[str(p) for p in report.graphs]}")
            print(f"Mapa de clímax sugeridos: {report.analytics.climax_map}")
            if report.analytics.pacing_alerts:
                print("Alertas de pacing:")
                for alert in report.analytics.pacing_alerts:
                    print(f"- {alert}")
        else:
            print("No se encontraron obras para procesar en modo automático.")
        return

    if args.source is None:
        raise SystemExit("Debes indicar una ruta de origen o activar --auto")

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
