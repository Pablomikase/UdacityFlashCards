"""Tests for utils.quiz_session (interactive loop + stats)."""

from __future__ import annotations

import io
from typing import Iterator, List

import pytest

from utils.data_loader import Flashcard
from utils.quiz_modes import SequentialMode
from utils.quiz_session import (
    EXIT_COMMANDS,
    SessionStats,
    is_correct,
    render_summary,
    run_session,
)


def _cards(*pairs: tuple) -> List[Flashcard]:
    return [Flashcard(front=f, back=b) for f, b in pairs]


def _scripted_input(answers: List[str]):
    """Build a stub for ``input`` that yields ``answers`` one prompt at a time.

    Raises ``AssertionError`` if the loop asks for more answers than the
    script provides — surfaces an over-eager loop as a test failure rather
    than a silent ``StopIteration``.
    """
    it: Iterator[str] = iter(answers)

    def fake_input(_prompt: str) -> str:
        try:
            return next(it)
        except StopIteration:  # pragma: no cover - defensive guard
            raise AssertionError("run_session requested more input than provided")

    return fake_input


# --- is_correct -------------------------------------------------------------


@pytest.mark.parametrize(
    "user, expected",
    [
        ("hello", "hello"),
        ("  hello  ", "hello"),
        ("HELLO", "hello"),
        ("Hello   World", "hello world"),
    ],
)
def test_is_correct_matches_with_normalization(user, expected):
    assert is_correct(user, expected) is True


@pytest.mark.parametrize(
    "user, expected",
    [
        ("hello", "world"),
        ("hello!", "hello"),  # punctuation is significant
        ("", "hello"),
    ],
)
def test_is_correct_rejects_mismatches(user, expected):
    assert is_correct(user, expected) is False


# --- SessionStats -----------------------------------------------------------


def test_session_stats_starts_empty():
    stats = SessionStats()
    assert stats.answered == 0
    assert stats.accuracy == 0.0


def test_session_stats_record_tracks_global_and_per_card():
    card = Flashcard("Q", "A")
    stats = SessionStats()
    stats.record(card, True)
    stats.record(card, False)
    stats.record(card, True)
    assert stats.correct == 2
    assert stats.incorrect == 1
    assert stats.answered == 3
    assert stats.accuracy == pytest.approx(2 / 3)
    assert stats.per_card["Q"] == {"correct": 2, "incorrect": 1}


# --- run_session ------------------------------------------------------------


def test_run_session_records_correct_and_incorrect_answers():
    cards = _cards(("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3"))
    quiz = SequentialMode(cards)
    out = io.StringIO()
    stats = run_session(
        quiz,
        input_fn=_scripted_input(["A1", "wrong", "a3"]),
        out=out,
        use_color=False,
    )
    assert stats.correct == 2
    assert stats.incorrect == 1
    assert stats.answered == 3
    assert "[OK] Correct!" in out.getvalue()
    assert "[X]  Incorrect. Expected: A2" in out.getvalue()


@pytest.mark.parametrize("exit_word", sorted(EXIT_COMMANDS))
def test_run_session_quits_on_exit_command(exit_word):
    quiz = SequentialMode(_cards(("Q1", "A1"), ("Q2", "A2")))
    out = io.StringIO()
    stats = run_session(
        quiz,
        input_fn=_scripted_input(["A1", exit_word]),
        out=out,
        use_color=False,
    )
    assert stats.answered == 1
    assert "Exiting quiz at user request." in out.getvalue()


def test_run_session_handles_keyboard_interrupt_gracefully():
    quiz = SequentialMode(_cards(("Q1", "A1")))
    out = io.StringIO()

    def raising_input(_prompt: str) -> str:
        raise KeyboardInterrupt

    stats = run_session(quiz, input_fn=raising_input, out=out, use_color=False)
    assert stats.answered == 0
    assert "Session interrupted" in out.getvalue()


def test_run_session_handles_eof_gracefully():
    quiz = SequentialMode(_cards(("Q1", "A1")))
    out = io.StringIO()

    def raising_input(_prompt: str) -> str:
        raise EOFError

    stats = run_session(quiz, input_fn=raising_input, out=out, use_color=False)
    assert stats.answered == 0
    assert "Session interrupted" in out.getvalue()


def test_run_session_completes_when_quiz_exhausts():
    cards = _cards(("Q1", "A1"))
    quiz = SequentialMode(cards)
    out = io.StringIO()
    stats = run_session(
        quiz,
        input_fn=_scripted_input(["A1"]),
        out=out,
        use_color=False,
    )
    assert stats.answered == 1
    # No "exit" / "interrupted" messaging when the deck ran out naturally.
    assert "Exiting" not in out.getvalue()
    assert "interrupted" not in out.getvalue()


def test_run_session_uses_ansi_when_color_forced_on():
    quiz = SequentialMode(_cards(("Q1", "A1")))
    out = io.StringIO()
    run_session(
        quiz,
        input_fn=_scripted_input(["A1"]),
        out=out,
        use_color=True,
    )
    # Green escape code must appear in the "Correct!" line.
    assert "\033[32m" in out.getvalue()


def test_run_session_omits_ansi_when_color_off():
    quiz = SequentialMode(_cards(("Q1", "A1")))
    out = io.StringIO()
    run_session(
        quiz,
        input_fn=_scripted_input(["wrong"]),
        out=out,
        use_color=False,
    )
    assert "\033[" not in out.getvalue()


# --- render_summary ---------------------------------------------------------


def test_render_summary_handles_empty_session():
    out = render_summary(SessionStats(), detailed=False, use_color=False)
    assert "No questions answered" in out


def test_render_summary_basic_totals():
    stats = SessionStats()
    stats.record(Flashcard("Q1", "A1"), True)
    stats.record(Flashcard("Q2", "A2"), False)
    summary = render_summary(stats, detailed=False, use_color=False)
    assert "Answered:  2" in summary
    assert "Correct:   1" in summary
    assert "Incorrect: 1" in summary
    assert "Accuracy:  50%" in summary
    # Without --stats we do not emit the per-card section.
    assert "Per-card breakdown" not in summary


def test_render_summary_detailed_includes_per_card_breakdown():
    stats = SessionStats()
    stats.record(Flashcard("Q1", "A1"), True)
    stats.record(Flashcard("Q2", "A2"), False)
    summary = render_summary(stats, detailed=True, use_color=False)
    assert "Per-card breakdown" in summary
    assert "Q1 (correct=1, incorrect=0)" in summary
    assert "Q2 (correct=0, incorrect=1)" in summary
