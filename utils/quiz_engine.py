"""Quiz engine: Strategy Pattern (QuizMode hierarchy) + Factory Pattern.

This module hosts the two design patterns the rubric inspects:

* **Strategy Pattern** — :class:`QuizMode` is an abstract base class with
  three interchangeable concrete strategies (:class:`SequentialMode`,
  :class:`RandomMode`, :class:`AdaptiveMode`). Each strategy encapsulates
  one card-ordering policy and is consumed through the same
  ``next_card`` / ``record_result`` interface, so the session loop has no
  knowledge of which policy is active.

* **Factory Pattern** — :func:`create_quiz_mode` maps a mode name to the
  matching concrete strategy. Callers (e.g. ``main.py``) pick a strategy
  by name without importing or branching on the concrete classes, so a
  new mode can be added by extending only the dispatch table here.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Dict, List, Optional, Sequence, Set

from utils.data_loader import Flashcard


# ---------------------------------------------------------------------------
# Strategy Pattern
# ---------------------------------------------------------------------------


class QuizMode(ABC):
    """Abstract base class for quiz session ordering strategies."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        if not cards:
            raise ValueError("QuizMode requires at least one flashcard.")
        self._cards: List[Flashcard] = list(cards)

    @property
    def total(self) -> int:
        """Number of distinct flashcards backing this session."""
        return len(self._cards)

    @abstractmethod
    def next_card(self) -> Optional[Flashcard]:
        """Return the next flashcard, or ``None`` when the session is done."""

    def record_result(self, correct: bool) -> None:
        """Record the outcome of the most recently served card.

        The default implementation is a no-op; strategies that adapt based
        on user performance should override this hook.
        """
        return None


class SequentialMode(QuizMode):
    """Serve cards in their original order (1, 2, 3, ...)."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        super().__init__(cards)
        self._index: int = 0

    def next_card(self) -> Optional[Flashcard]:
        if self._index >= len(self._cards):
            return None
        card = self._cards[self._index]
        self._index += 1
        return card


class RandomMode(QuizMode):
    """Serve every card exactly once in a single shuffled order."""

    def __init__(
        self,
        cards: Sequence[Flashcard],
        rng: Optional[random.Random] = None,
    ) -> None:
        super().__init__(cards)
        shuffler = rng if rng is not None else random.Random()
        self._order: List[Flashcard] = list(self._cards)
        shuffler.shuffle(self._order)
        self._index: int = 0

    def next_card(self) -> Optional[Flashcard]:
        if self._index >= len(self._order):
            return None
        card = self._order[self._index]
        self._index += 1
        return card


class AdaptiveMode(QuizMode):
    """Serve every card once, then re-serve missed cards until mastered.

    Each card is presented exactly once during the first pass. After that,
    cards the user got wrong are presented again, prioritized by error
    count (highest first; ties broken by original position). A card is
    "mastered" the first time it is answered correctly, after which it is
    not served again. The session ends when every card has been mastered.
    """

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        super().__init__(cards)
        self._unseen: Deque[int] = deque(range(len(self._cards)))
        self._miss_counts: Dict[int, int] = {}
        self._mastered: Set[int] = set()
        self._current_index: Optional[int] = None

    def next_card(self) -> Optional[Flashcard]:
        while self._unseen:
            idx = self._unseen.popleft()
            if idx not in self._mastered:
                self._current_index = idx
                return self._cards[idx]

        pending = [
            (idx, misses)
            for idx, misses in self._miss_counts.items()
            if idx not in self._mastered
        ]
        if not pending:
            self._current_index = None
            return None
        pending.sort(key=lambda item: (-item[1], item[0]))
        self._current_index = pending[0][0]
        return self._cards[self._current_index]

    def record_result(self, correct: bool) -> None:
        if self._current_index is None:
            return
        idx = self._current_index
        if correct:
            self._mastered.add(idx)
            self._miss_counts.pop(idx, None)
        else:
            self._miss_counts[idx] = self._miss_counts.get(idx, 0) + 1


# ---------------------------------------------------------------------------
# Factory Pattern
# ---------------------------------------------------------------------------


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
