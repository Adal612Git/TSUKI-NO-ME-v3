from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Scene:
    text: str
    start: int
    end: int
    index: int


def segment_text(text: str, max_scene_chars: int = 1200) -> List[Scene]:
    """Segment text using heuristic boundaries.

    Priority is given to paragraph boundaries; if a paragraph exceeds the
    maximum size, it will be split by character windows.
    """

    scenes: List[Scene] = []
    cursor = 0
    paragraphs = text.split("\n\n")

    for idx, paragraph in enumerate(paragraphs):
        block = paragraph.strip()
        if not block:
            cursor += len(paragraph) + 2
            continue

        start = cursor
        while len(block) > max_scene_chars:
            chunk = block[:max_scene_chars]
            end = start + len(chunk)
            scenes.append(Scene(text=chunk, start=start, end=end, index=len(scenes)))
            block = block[max_scene_chars:]
            start = end
        end = start + len(block)
        scenes.append(Scene(text=block, start=start, end=end, index=len(scenes)))
        cursor += len(paragraph) + 2

    return scenes
