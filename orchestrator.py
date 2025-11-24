"""Master orchestrator for Project Uzumaki."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from uzumaki.data_cleaner import DataCleaner
from uzumaki.metrics import (
    calculate_arc_satisfaction,
    calculate_character_balance,
    calculate_pacing_score,
    flag_filler_arcs,
    identify_overused_tropes,
)
from uzumaki.models import CharacterPopularity, EpisodeRating, StoryArc, Trope
from uzumaki.reporting import ReportGenerator
from uzumaki.scraping.fandom import FandomScraper
from uzumaki.scraping.imdb import IMDBScraper
from uzumaki.scraping.mal import MALScraper
from uzumaki.scraping.tvtropes import TVTropesScraper

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, output_dir: str = "data") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.cleaner = DataCleaner()
        self.reporter = ReportGenerator()

    def run_scrapers(self) -> None:
        logger.info("Starting scraper suite")
        mal = MALScraper()
        characters = mal.fetch_characters()
        mal.dump_checkpoint(characters, self.output_dir / "mal_characters.tsv")
        self.cleaner.add_characters(characters)

        fandom_arcs = FandomScraper().fetch()
        self.cleaner.add_arcs(fandom_arcs)

        tv_tropes = TVTropesScraper().fetch()
        self.cleaner.add_tropes(tv_tropes)

        with IMDBScraper() as imdb:
            episodes = imdb.fetch_all()
        self.cleaner.add_episodes(episodes)

        # Persist cleaned dataset
        self.cleaner.to_sqlite(str(self.output_dir / "naruto_analysis.db"))
        self.cleaner.snapshot_to_excel(str(self.output_dir / "naruto_analysis.xlsx"))

    def compute_metrics(self) -> dict:
        logger.info("Computing metrics from cleaned dataset")
        dataset = self.cleaner.dataset
        pacing = {arc.name: calculate_pacing_score(arc) for arc in dataset.arcs}
        satisfaction = {
            arc.name: calculate_arc_satisfaction(arc, dataset.episodes)
            for arc in dataset.arcs
        }
        balance = calculate_character_balance(dataset.characters)
        tropes = identify_overused_tropes(dataset.tropes)
        filler = flag_filler_arcs(dataset.arcs, dataset.episodes)
        metrics = {
            "pacing": pacing,
            "satisfaction": satisfaction,
            "character_balance": balance,
            "overused_tropes": tropes,
            "filler": [(arc.name, score) for arc, score in filler],
        }
        (self.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return metrics

    def build_report(self, metrics: dict | None = None) -> str:
        metrics = metrics or self.compute_metrics()
        html = self.reporter.render_html(
            arcs=self.cleaner.dataset.arcs,
            episodes=self.cleaner.dataset.episodes,
            characters=self.cleaner.dataset.characters,
            tropes=self.cleaner.dataset.tropes,
            executive_summary=self._summary_from_metrics(metrics),
        )
        html_path = self.output_dir / "report.html"
        self.reporter.save_html(html, str(html_path))
        return str(html_path)

    def _summary_from_metrics(self, metrics: dict) -> list[str]:
        summary: list[str] = []
        pacing = metrics.get("pacing", {})
        if pacing:
            worst = sorted(
                [(arc, score) for arc, score in pacing.items() if score],
                key=lambda item: item[1],
                reverse=True,
            )
            if worst:
                summary.append(
                    f"El arco peor ritmado es '{worst[0][0]}' con score {worst[0][1]:.2f}."
                )
        balance = metrics.get("character_balance", {})
        if balance:
            top = sorted(balance.items(), key=lambda item: item[1], reverse=True)[:3]
            summary.append(
                "Personajes con mayor tracción: "
                + ", ".join(f"{name} ({pct:.1f}%)" for name, pct in top)
            )
        return summary


def main() -> None:
    orchestrator = Orchestrator()
    orchestrator.run_scrapers()
    metrics = orchestrator.compute_metrics()
    report_path = orchestrator.build_report(metrics)
    logger.info("Reporte generado en %s", report_path)


if __name__ == "__main__":
    main()
