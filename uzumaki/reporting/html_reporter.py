"""HTML report generation with resilience to missing datasets."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, select_autoescape

from uzumaki.metrics import calculate_pacing_score, identify_overused_tropes
from uzumaki.models import CharacterPopularity, EpisodeRating, StoryArc, Trope

logger = logging.getLogger(__name__)


def _character_balance_series(characters: Iterable[CharacterPopularity]) -> Dict[str, float]:
    total = sum(c.favorites for c in characters)
    return {c.name: (c.favorites / total) * 100 if total else 0 for c in characters}


class HTMLReporter:
    def __init__(self, template_dir: str | None = None) -> None:
        self.template_dir = template_dir or str(Path(__file__).resolve().parent.parent / "templates")
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_html(
        self,
        *,
        arcs: Iterable[StoryArc],
        episodes: Iterable[EpisodeRating],
        characters: Iterable[CharacterPopularity],
        tropes: Iterable[Trope],
        executive_summary: List[str] | None = None,
    ) -> str:
        template = self.env.get_template("report.html")
        balance = _character_balance_series(characters)
        pacing_scores = [(arc.name, calculate_pacing_score(arc)) for arc in arcs]
        overused_tropes = identify_overused_tropes(tropes)

        context = {
            "title": "Análisis Narrativo de Naruto Shippuden - Project Uzumaki",
            "executive_summary": executive_summary or [],
            "pacing_scores": pacing_scores,
            "overused_tropes": overused_tropes,
            "character_balance": balance,
            "arc_satisfaction_plot": self._plot_arc_satisfaction(arcs, episodes),
            "character_balance_plot": self._plot_character_balance(balance),
        }
        return template.render(**context)

    def _plot_arc_satisfaction(self, arcs: Iterable[StoryArc], episodes: Iterable[EpisodeRating]) -> str:
        scores: Dict[str, float] = {}
        rated = [e.rating for e in episodes if e.rating is not None]
        if rated:
            mean_rating = sum(rated) / len(rated)
            for arc in arcs:
                scores[arc.name] = mean_rating
        if not scores:
            return ""
        fig, ax = plt.subplots(figsize=(8, 4))
        names, values = zip(*scores.items())
        ax.plot(names, values, marker="o")
        ax.set_ylabel("IMDb Rating Promedio")
        ax.set_xticklabels(names, rotation=45, ha="right")
        output = Path("artifacts") / "arc_satisfaction.png"
        output.parent.mkdir(exist_ok=True)
        fig.tight_layout()
        fig.savefig(output)
        plt.close(fig)
        return str(output)

    def _plot_character_balance(self, balance: Dict[str, float]) -> str:
        if not balance:
            return ""
        fig, ax = plt.subplots(figsize=(6, 6))
        names, values = zip(*balance.items())
        ax.pie(values, labels=names, autopct="%1.1f%%")
        output = Path("artifacts") / "character_balance.png"
        output.parent.mkdir(exist_ok=True)
        fig.savefig(output)
        plt.close(fig)
        return str(output)

    def save_html(self, html: str, path: str) -> None:
        logger.info("Writing HTML report to %s", path)
        Path(path).write_text(html, encoding="utf-8")
