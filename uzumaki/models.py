"""Data models for Project Uzumaki."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EpisodeRating:
    season: int
    episode: int
    title: str
    rating: Optional[float]
    votes: Optional[int]


@dataclass
class CharacterPopularity:
    name: str
    profile_url: str
    favorites: int


@dataclass
class StoryArc:
    name: str
    start_episode: Optional[int]
    end_episode: Optional[int]
    synopsis: str
    is_filler: bool = False
    manga_chapters: Optional[int] = None
    anime_episodes: Optional[int] = None


@dataclass
class Trope:
    name: str
    category: str
    frequency: int


@dataclass
class CleanedDataset:
    episodes: List[EpisodeRating] = field(default_factory=list)
    characters: List[CharacterPopularity] = field(default_factory=list)
    arcs: List[StoryArc] = field(default_factory=list)
    tropes: List[Trope] = field(default_factory=list)
