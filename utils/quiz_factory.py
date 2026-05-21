"""Factory Pattern: build :class:`QuizMode` instances from a mode name.

Centralizing construction here keeps the CLI (and any future entry point)
decoupled from the concrete strategy classes — new modes can be added by
extending the dispatch table here without touching callers.
"""

from __future__ import annotations

import random
from typing import Optional, Sequence

from utils.data_loader import Flashcard
from utils.quiz_modes import AdaptiveMode, QuizMode, RandomMode, SequentialMode

QUIZ_MODES = ("sequential", "random", "adaptive")


class UnknownQuizModeError(ValueError):
    """Raised when the requested quiz mode name is not recognized."""


def create_quiz_mode(
    mode_name: str,
    cards: Sequence[Flashcard],
    *,
    rng: Optional[random.Random] = None,
) -> QuizMode:
    """Build the :class:`QuizMode` strategy named by ``mode_name``.

    Args:
        mode_name: Case-insensitive mode identifier (leading/trailing
            whitespace is tolerated). Must be one of :data:`QUIZ_MODES`.
        cards: Flashcards the session will draw from.
        rng: Optional ``random.Random`` used by :class:`RandomMode` to
            produce deterministic shuffles in tests. Ignored by other
            modes.

    Raises:
        UnknownQuizModeError: If ``mode_name`` is not a recognized mode.
    """
    name = mode_name.strip().lower()
    if name == "sequential":
        return SequentialMode(cards)
    if name == "random":
        return RandomMode(cards, rng=rng)
    if name == "adaptive":
        return AdaptiveMode(cards)
    raise UnknownQuizModeError(
        f"Unknown quiz mode: {mode_name!r}. "
        f"Valid modes: {', '.join(QUIZ_MODES)}."
    )
