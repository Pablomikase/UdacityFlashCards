"""Strategy Pattern: ``QuizMode`` and its concrete implementations.

Each :class:`QuizMode` subclass encapsulates one ordering strategy for
serving flashcards during a quiz session. Callers consume cards through
:meth:`QuizMode.next_card` and report outcomes through
:meth:`QuizMode.record_result`. The base class records nothing by default,
so strategies that do not adapt (Sequential, Random) need not override the
result hook.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Dict, List, Optional, Sequence, Set

from utils.data_loader import Flashcard


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
