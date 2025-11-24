"""IMDb scraper powered by IMDbPY (no Selenium)."""
from __future__ import annotations

import logging
from typing import List

from imdb import Cinemagoer, IMDbError

from uzumaki.cleaning import deduplicate_by, normalize_whitespace
from uzumaki.models import EpisodeRating

logger = logging.getLogger(__name__)


class IMDBApiScraper:
    def __init__(self, show_id: str = "0409591", client: Cinemagoer | None = None) -> None:
        self.show_id = show_id
        self.client = client or Cinemagoer()

    def fetch_all(self) -> List[EpisodeRating]:
        logger.info("Fetching episodes and ratings via IMDbPY for show %s", self.show_id)
        try:
            show = self.client.get_movie(self.show_id)
            self.client.update(show, "episodes")
        except IMDbError as exc:
            logger.warning("IMDbPY failed to retrieve show %s: %s", self.show_id, exc)
            return []

        episodes_map = show.get("episodes", {}) if show else {}
        episodes: list[EpisodeRating] = []
        for season_number, season_episodes in sorted(episodes_map.items()):
            for episode_number, episode_obj in sorted(season_episodes.items()):
                title = normalize_whitespace(episode_obj.get("title")) or "Unknown"
                rating = episode_obj.get("rating")
                votes = episode_obj.get("votes")
                episodes.append(
                    EpisodeRating(
                        season=int(season_number),
                        episode=int(episode_number),
                        title=title,
                        rating=float(rating) if rating is not None else None,
                        votes=int(votes) if votes is not None else None,
                    )
                )
        episodes = deduplicate_by(episodes, lambda e: f"{e.season}-{e.episode}-{e.title.lower()}")
        logger.info("Collected %d episodes from IMDbPY", len(episodes))
        return episodes
