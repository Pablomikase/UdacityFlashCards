"""Load and validate flashcard data from JSON files.

Supports two top-level JSON shapes:

  1. A bare array of cards: ``[{"front": "...", "back": "..."}, ...]``
  2. A wrapper object:      ``{"cards": [{"front": "...", "back": "..."}, ...]}``

Any structural or I/O problem is surfaced as :class:`FlashcardDataError`
with a human-readable message — callers never see raw tracebacks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Sequence


@dataclass(frozen=True)
class Flashcard:
    """A single flashcard with a prompt (``front``) and answer (``back``)."""

    front: str
    back: str


class FlashcardDataError(Exception):
    """Raised when flashcard data cannot be loaded or validated.

    The message is intended to be printed directly to the user, so callers
    should not wrap it in additional framing.
    """


def load_flashcards(path: Path) -> List[Flashcard]:
    """Load and validate flashcards from a JSON file at ``path``.

    Accepts either a bare array of cards or a wrapper object containing a
    ``"cards"`` array. Each card must be a JSON object with non-empty string
    ``"front"`` and ``"back"`` fields.

    Raises:
        FlashcardDataError: If the file cannot be read, the JSON is
            malformed, or the data does not match either accepted shape.
    """
    raw_text = _read_text(path)
    data = _parse_json(raw_text, path)
    raw_cards = _extract_cards_array(data, path)
    return _validate_cards(raw_cards, path)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FlashcardDataError(f"File not found: {path}") from None
    except PermissionError:
        raise FlashcardDataError(f"Permission denied when reading {path}.") from None
    except OSError as err:
        raise FlashcardDataError(f"Could not read {path}: {err}") from None


def _parse_json(raw_text: str, path: Path) -> Any:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as err:
        raise FlashcardDataError(
            f"{path} is not valid JSON: {err.msg} "
            f"(line {err.lineno}, column {err.colno})."
        ) from None


def _extract_cards_array(data: Any, path: Path) -> Sequence[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "cards" not in data:
            raise FlashcardDataError(
                f"{path} is an object but is missing the required " f"'cards' field."
            )
        cards = data["cards"]
        if not isinstance(cards, list):
            raise FlashcardDataError(f"{path}: the 'cards' field must be a JSON array.")
        return cards
    raise FlashcardDataError(
        f"{path} must be either a JSON array of cards or an object "
        f"with a 'cards' array."
    )


def _validate_cards(raw_cards: Sequence[Any], path: Path) -> List[Flashcard]:
    if not raw_cards:
        raise FlashcardDataError(
            f"{path} contains zero flashcards — at least one is required."
        )
    cards: List[Flashcard] = []
    for index, raw in enumerate(raw_cards, start=1):
        cards.append(_build_card(raw, index, path))
    return cards


def _build_card(raw: Any, index: int, path: Path) -> Flashcard:
    if not isinstance(raw, dict):
        raise FlashcardDataError(f"Card #{index} in {path} must be a JSON object.")
    front = raw.get("front")
    back = raw.get("back")
    if not isinstance(front, str) or not front.strip():
        raise FlashcardDataError(
            f"Card #{index} in {path} is missing a non-empty string " f"'front' field."
        )
    if not isinstance(back, str) or not back.strip():
        raise FlashcardDataError(
            f"Card #{index} in {path} is missing a non-empty string " f"'back' field."
        )
    return Flashcard(front=front, back=back)
