from __future__ import annotations

import math
import re
from dataclasses import dataclass
from statistics import mean, variance
from typing import List

from narrative_quantifier.db.models import SceneVector, TempoMetrics

POSITIVE_WORDS = {
    "victory",
    "hope",
    "alegría",
    "bravo",
    "hero",
    "rescate",
    "logro",
}
NEGATIVE_WORDS = {
    "miedo",
    "derrota",
    "odio",
    "pérdida",
    "llanto",
    "fracaso",
    "traición",
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\w']+", text.lower())


def sentiment_score(text: str) -> float:
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    positives = sum(1 for t in tokens if t in POSITIVE_WORDS)
    negatives = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    return (positives - negatives) / len(tokens)


def lexical_complexity(text: str) -> float:
    sentences = re.split(r"[.!?]", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = _tokenize(text)
    if not sentences or not words:
        return 0.0
    avg_sentence_length = sum(len(_tokenize(s)) for s in sentences) / len(sentences)
    avg_word_length = sum(len(w) for w in words) / len(words)
    syllable_estimate = sum(_estimate_syllables(w) for w in words) / len(words)
    return avg_sentence_length * 0.6 + avg_word_length * 2.0 + syllable_estimate


def _estimate_syllables(word: str) -> float:
    return max(1, len(re.findall(r"[aeiouyáéíóúü]", word)))


def tempo_metrics(text: str) -> TempoMetrics:
    words = _tokenize(text)
    sentences = max(1, len(re.split(r"[.!?]", text)))
    wps = len(words) / sentences
    tempo_shift = (wps - 5.0) / 5.0
    return TempoMetrics(wps=wps, tempo_shift=tempo_shift)


def dta_ratio(text: str) -> float:
    words = _tokenize(text)
    if not words:
        return 0.0
    dialogue_tokens = sum(1 for t in words if t.startswith("\""))
    action_tokens = len(words) - dialogue_tokens
    if action_tokens == 0:
        return 1.0
    return dialogue_tokens / action_tokens


def emotional_volatility(sentiments: List[float]) -> float:
    if len(sentiments) < 2:
        return 0.0
    return math.sqrt(variance(sentiments))


def novelty_score(current_tokens: List[str], history: List[List[str]], window: int = 12) -> float:
    if not current_tokens:
        return 0.0
    prior = history[-window:]
    if not prior:
        return 1.0
    prior_vocab = set(token for scene_tokens in prior for token in scene_tokens)
    novelty = len([t for t in current_tokens if t not in prior_vocab]) / len(current_tokens)
    return novelty


def internal_change(text: str, previous_text: str | None) -> float:
    if not previous_text:
        return 0.0
    current_tokens = set(_tokenize(text))
    previous_tokens = set(_tokenize(previous_text))
    if not previous_tokens:
        return 0.0
    symmetric_diff = current_tokens.symmetric_difference(previous_tokens)
    return len(symmetric_diff) / max(1, len(previous_tokens))


def build_scene_vector(
    text: str,
    previous_text: str | None,
    history_tokens: List[List[str]],
    novelty_window: int,
) -> SceneVector:
    tokens = _tokenize(text)
    sentiment = sentiment_score(text)
    complexity = lexical_complexity(text)
    feat_magnitude = _feat_magnitude(text)
    novelty = novelty_score(tokens, history_tokens, window=novelty_window)
    change = internal_change(text, previous_text)
    return SceneVector(
        S_t=sentiment,
        L_t=complexity,
        F_t=feat_magnitude,
        N_t=novelty,
        I_t=change,
    )


POWER_KEYWORDS = {
    "chakra",
    "poder",
    "explosión",
    "invencible",
    "golpe",
    "espada",
    "magia",
    "jinchuriki",
}


def _feat_magnitude(text: str) -> float:
    tokens = _tokenize(text)
    hits = sum(1 for t in tokens if t in POWER_KEYWORDS)
    return math.log1p(hits)
