"""End-to-end integration tests for the FlashcardQuizzer pipeline.

These tests wire together the real data loader, factory and session loop
against a temporary JSON glossary on disk, so they exercise the same path
the CLI takes — only the ``input`` callable is stubbed out to drive the
loop deterministically.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Iterator, List

import pytest

from utils.data_loader import load_flashcards
from utils.quiz_factory import create_quiz_mode
from utils.quiz_session import render_summary, run_session


def _write_glossary(path: Path, pairs: List[tuple]) -> Path:
    """Drop a JSON glossary on disk and return its path."""
    payload = [{"front": front, "back": back} for front, back in pairs]
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _scripted_input(answers: List[str]):
    """Build a fake ``input`` callable that yields ``answers`` one prompt at a time."""
    it: Iterator[str] = iter(answers)

    def fake_input(_prompt: str) -> str:
        return next(it)

    return fake_input


def test_full_session(tmp_path: Path):
    """Load a glossary, run a 3-question session, and verify final stats."""
    glossary = _write_glossary(
        tmp_path / "glossary.json",
        [
            ("capital of France", "Paris"),
            ("2 + 2", "4"),
            ("color of the sky", "blue"),
        ],
    )

    # Stage 1 — loader: returns three cards in input order.
    cards = load_flashcards(glossary)
    assert len(cards) == 3

    # Stage 2 — factory: build the deterministic Sequential strategy.
    quiz = create_quiz_mode("sequential", cards)

    # Stage 3 — session: simulate the user answering Q1 correctly,
    # Q2 incorrectly, and Q3 correctly (with a different casing to also
    # exercise the case-insensitive comparison).
    out = io.StringIO()
    stats = run_session(
        quiz,
        input_fn=_scripted_input(["Paris", "five", "BLUE"]),
        out=out,
        use_color=False,
    )

    # Stage 4 — final stats calculation.
    assert stats.answered == 3
    assert stats.correct == 2
    assert stats.incorrect == 1
    assert stats.accuracy == pytest.approx(2 / 3)

    # Per-card breakdown reflects each individual question's outcome.
    assert stats.per_card["capital of France"] == {"correct": 1, "incorrect": 0}
    assert stats.per_card["2 + 2"] == {"correct": 0, "incorrect": 1}
    assert stats.per_card["color of the sky"] == {"correct": 1, "incorrect": 0}

    # Stage 5 — summary renderer agrees with the raw stats.
    summary = render_summary(stats, detailed=True, use_color=False)
    assert "Answered:  3" in summary
    assert "Correct:   2" in summary
    assert "Incorrect: 1" in summary
    assert "Accuracy:  67%" in summary
    assert "capital of France (correct=1, incorrect=0)" in summary
    assert "2 + 2 (correct=0, incorrect=1)" in summary

    # And the loop printed feedback for every question, including the
    # expected answer on the one the user got wrong.
    transcript = out.getvalue()
    assert transcript.count("[OK] Correct!") == 2
    assert "[X]  Incorrect. Expected: 4" in transcript
