"""Tests for utils.quiz_factory (Factory Pattern)."""

from __future__ import annotations

import random

import pytest

from utils.data_loader import Flashcard
from utils.quiz_factory import (
    QUIZ_MODES,
    UnknownQuizModeError,
    create_quiz_mode,
)
from utils.quiz_modes import AdaptiveMode, RandomMode, SequentialMode


@pytest.fixture()
def cards():
    return [Flashcard(front=f, back=f"ans-{f}") for f in ("a", "b", "c")]


def test_creates_sequential_mode(cards):
    assert isinstance(create_quiz_mode("sequential", cards), SequentialMode)


def test_creates_random_mode(cards):
    assert isinstance(create_quiz_mode("random", cards), RandomMode)


def test_creates_adaptive_mode(cards):
    assert isinstance(create_quiz_mode("adaptive", cards), AdaptiveMode)


def test_mode_name_is_case_insensitive(cards):
    assert isinstance(create_quiz_mode("SEQUENTIAL", cards), SequentialMode)
    assert isinstance(create_quiz_mode("Random", cards), RandomMode)
    assert isinstance(create_quiz_mode("aDaPtIvE", cards), AdaptiveMode)


def test_mode_name_tolerates_whitespace(cards):
    assert isinstance(create_quiz_mode("  random  ", cards), RandomMode)


def test_unknown_mode_raises_friendly_error(cards):
    with pytest.raises(UnknownQuizModeError, match="Unknown quiz mode"):
        create_quiz_mode("brain-dump", cards)


def test_unknown_quiz_mode_error_is_value_error(cards):
    # Subclassing ValueError keeps the factory friendly for callers that
    # only catch the standard exception type.
    with pytest.raises(ValueError):
        create_quiz_mode("nope", cards)


def test_random_mode_receives_rng_for_determinism(cards):
    a = create_quiz_mode("random", cards, rng=random.Random(7))
    b = create_quiz_mode("random", cards, rng=random.Random(7))
    order_a = [a.next_card() for _ in cards]
    order_b = [b.next_card() for _ in cards]
    assert order_a == order_b


def test_rng_is_ignored_for_non_random_modes(cards):
    # Should not raise; rng simply has no effect on Sequential/Adaptive.
    seq = create_quiz_mode("sequential", cards, rng=random.Random(0))
    adapt = create_quiz_mode("adaptive", cards, rng=random.Random(0))
    assert isinstance(seq, SequentialMode)
    assert isinstance(adapt, AdaptiveMode)


def test_quiz_modes_tuple_covers_every_supported_name(cards):
    for name in QUIZ_MODES:
        assert create_quiz_mode(name, cards) is not None


def test_empty_cards_propagates_value_error():
    with pytest.raises(ValueError, match="at least one flashcard"):
        create_quiz_mode("sequential", [])
