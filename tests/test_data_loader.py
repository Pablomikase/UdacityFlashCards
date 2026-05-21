"""Tests for utils.data_loader."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from utils.data_loader import Flashcard, FlashcardDataError, load_flashcards


# --- happy paths ------------------------------------------------------------


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_array_format_loads(tmp_path):
    p = _write(tmp_path / "g.json", [{"front": "Q", "back": "A"}])
    assert load_flashcards(p) == [Flashcard("Q", "A")]


def test_object_format_loads(tmp_path):
    p = _write(tmp_path / "g.json", {"cards": [{"front": "Q", "back": "A"}]})
    assert load_flashcards(p) == [Flashcard("Q", "A")]


def test_object_format_ignores_extra_top_level_fields(tmp_path):
    p = _write(
        tmp_path / "g.json",
        {"title": "OOP", "cards": [{"front": "Q", "back": "A"}]},
    )
    assert load_flashcards(p) == [Flashcard("Q", "A")]


def test_multiple_cards_preserve_order(tmp_path):
    p = _write(
        tmp_path / "g.json",
        [
            {"front": "a", "back": "1"},
            {"front": "b", "back": "2"},
            {"front": "c", "back": "3"},
        ],
    )
    cards = load_flashcards(p)
    assert [c.front for c in cards] == ["a", "b", "c"]
    assert [c.back for c in cards] == ["1", "2", "3"]


def test_loaded_flashcards_are_immutable(tmp_path):
    p = _write(tmp_path / "g.json", [{"front": "Q", "back": "A"}])
    card = load_flashcards(p)[0]
    with pytest.raises(Exception):
        card.front = "tampered"  # frozen dataclass


# --- I/O errors -------------------------------------------------------------


def test_missing_file_raises_friendly_error(tmp_path):
    with pytest.raises(FlashcardDataError, match="File not found"):
        load_flashcards(tmp_path / "missing.json")


def test_malformed_json_raises_friendly_error(tmp_path):
    p = tmp_path / "g.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(FlashcardDataError, match="not valid JSON"):
        load_flashcards(p)


@pytest.mark.skipif(os.name == "nt", reason="chmod semantics differ on Windows")
def test_unreadable_file_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", [{"front": "Q", "back": "A"}])
    p.chmod(0o000)
    try:
        with pytest.raises(FlashcardDataError, match="Permission denied"):
            load_flashcards(p)
    finally:
        p.chmod(0o644)


# --- top-level shape errors -------------------------------------------------


def test_wrong_top_level_type_string_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", "oops")
    with pytest.raises(FlashcardDataError, match="JSON array of cards or an object"):
        load_flashcards(p)


def test_wrong_top_level_type_number_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", 42)
    with pytest.raises(FlashcardDataError, match="JSON array of cards or an object"):
        load_flashcards(p)


def test_object_missing_cards_field_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", {"items": []})
    with pytest.raises(FlashcardDataError, match="missing the required 'cards'"):
        load_flashcards(p)


def test_object_cards_field_not_array_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", {"cards": "nope"})
    with pytest.raises(FlashcardDataError, match="'cards' field must be a JSON array"):
        load_flashcards(p)


def test_empty_array_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", [])
    with pytest.raises(FlashcardDataError, match="zero flashcards"):
        load_flashcards(p)


def test_empty_cards_array_in_object_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", {"cards": []})
    with pytest.raises(FlashcardDataError, match="zero flashcards"):
        load_flashcards(p)


# --- per-card shape errors --------------------------------------------------


def test_non_object_card_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", ["just a string"])
    with pytest.raises(FlashcardDataError, match=r"Card #1 .* must be a JSON object"):
        load_flashcards(p)


def test_missing_front_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", [{"back": "A"}])
    with pytest.raises(FlashcardDataError, match="non-empty string 'front' field"):
        load_flashcards(p)


def test_missing_back_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", [{"front": "Q"}])
    with pytest.raises(FlashcardDataError, match="non-empty string 'back' field"):
        load_flashcards(p)


def test_non_string_front_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", [{"front": 42, "back": "A"}])
    with pytest.raises(FlashcardDataError, match="non-empty string 'front' field"):
        load_flashcards(p)


def test_blank_back_raises_friendly_error(tmp_path):
    p = _write(tmp_path / "g.json", [{"front": "Q", "back": "   "}])
    with pytest.raises(FlashcardDataError, match="non-empty string 'back' field"):
        load_flashcards(p)


def test_second_card_invalid_reports_correct_index(tmp_path):
    p = _write(
        tmp_path / "g.json",
        [{"front": "ok", "back": "ok"}, {"front": "", "back": "x"}],
    )
    with pytest.raises(FlashcardDataError, match=r"Card #2"):
        load_flashcards(p)
