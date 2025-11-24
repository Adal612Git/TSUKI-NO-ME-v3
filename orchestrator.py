"""Master orchestrator for Project Uzumaki."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from uzumaki.data_cleaner import DataCleaner
from uzumaki.metrics import (
    calculate_arc_satisfaction,
    calculate_character_balance,
    calculate_pacing_score,
    flag_filler_arcs,
    identify_overused_tropes,
)
from uzumaki.reporting import HTMLReporter
from uzumaki.scraping import FandomAPIClient, IMDBApiScraper, MALScraper, TVTropesLiteScraper
from uzumaki.scraping.base import run_in_executor

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, output_dir: str = "data") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.cleaner = DataCleaner()
        self.reporter = HTMLReporter()

    def run_scrapers(self) -> None:
        asyncio.run(self._run_scrapers_async())

    async def _run_scrapers_async(self) -> None:
        logger.info("Starting scraper suite (async)")
        mal = MALScraper()
        fandom = FandomAPIClient()
        tv_tropes = TVTropesLiteScraper()
        imdb = IMDBApiScraper()

        async with fandom, tv_tropes:
            characters_task = run_in_executor(mal.fetch_characters)
            arcs_task = asyncio.create_task(fandom.fetch_arcs())
            tropes_task = asyncio.create_task(tv_tropes.fetch())
            episodes_task = run_in_executor(imdb.fetch_all)

            characters, fandom_arcs, tv_tropes_list, episodes = await asyncio.gather(
                characters_task, arcs_task, tropes_task, episodes_task
            )

        if not characters:
            logger.warning("MAL scraper returned no characters; downstream metrics may be limited")
        if not fandom_arcs:
            logger.warning("Fandom scraper returned no arcs; pacing metrics will be skipped")
        if not tv_tropes_list:
            logger.warning("TVTropes scraper returned no tropes; trope analysis will be empty")
        if not episodes:
            logger.warning("IMDb scraper returned no episodes; episode metrics will be unavailable")

        if characters:
            self.cleaner.add_characters(characters)
        if fandom_arcs:
            self.cleaner.add_arcs(fandom_arcs)
        if tv_tropes_list:
            self.cleaner.add_tropes(tv_tropes_list)
        if episodes:
            self.cleaner.add_episodes(episodes)

        self._persist_cleaned_dataset()

    def _persist_cleaned_dataset(self) -> None:
        # Persist cleaned dataset with resilient writers
        sqlite_path = self.output_dir / "naruto_analysis.db"
        excel_path = self.output_dir / "naruto_analysis.xlsx"
        parquet_dir = self.output_dir / "parquet"
        self.cleaner.to_sqlite(str(sqlite_path))
        self.cleaner.snapshot_to_excel(str(excel_path))
        self.cleaner.snapshot_to_parquet(str(parquet_dir))

    def compute_metrics(self) -> dict:
        logger.info("Computing metrics from cleaned dataset")
        dataset = self.cleaner.dataset
        metrics: dict = {}

        if dataset.arcs:
            pacing = {arc.name: calculate_pacing_score(arc) for arc in dataset.arcs}
            satisfaction = {
                arc.name: calculate_arc_satisfaction(arc, dataset.episodes)
                for arc in dataset.arcs
            }
            metrics["pacing"] = pacing
            metrics["satisfaction"] = satisfaction
            metrics["filler"] = [(arc.name, score) for arc, score in flag_filler_arcs(dataset.arcs, dataset.episodes)]
        else:
            logger.warning("Skipping arc-based metrics: no arcs available")

        if dataset.characters:
            metrics["character_balance"] = calculate_character_balance(dataset.characters)
        else:
            logger.warning("Skipping character balance metric: no characters available")

        if dataset.tropes:
            metrics["overused_tropes"] = identify_overused_tropes(dataset.tropes)
        else:
            logger.warning("Skipping trope analysis: no tropes available")

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
