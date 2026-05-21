"""Interactive quiz session loop and end-of-session statistics reporter.

The :func:`run_session` coroutine drives a :class:`~utils.quiz_modes.QuizMode`
through its cards, prompting the user for an answer per card and recording
the outcome on both the strategy (so adaptive modes can re-serve missed
cards) and a :class:`SessionStats` accumulator (used to render the final
summary). The loop is decoupled from ``stdin``/``stdout`` via the
``input_fn`` and ``out`` parameters, which makes the loop trivially
testable.

Graceful-exit handling lives here too: typing one of :data:`EXIT_COMMANDS`,
sending EOF (Ctrl+D), or sending SIGINT (Ctrl+C) all break out of the loop
and return the partial stats so callers can still print a summary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import IO, Callable, Dict, Optional

from utils.colors import (
    BOLD,
    CYAN,
    DIM,
    YELLOW,
    colorize,
    colors_enabled,
    green,
    red,
)
from utils.data_loader import Flashcard
from utils.quiz_modes import QuizMode

EXIT_COMMANDS = frozenset({"exit", "quit", ":q"})


@dataclass
class SessionStats:
    """Running tally of correct/incorrect answers for one quiz session."""

    correct: int = 0
    incorrect: int = 0
    per_card: Dict[str, Dict[str, int]] = field(default_factory=dict)

    @property
    def answered(self) -> int:
        """Total prompts the user actually answered (correct + incorrect)."""
        return self.correct + self.incorrect

    @property
    def accuracy(self) -> float:
        """Fraction in ``[0.0, 1.0]``; ``0.0`` when no prompts were answered."""
        return (self.correct / self.answered) if self.answered else 0.0

    def record(self, card: Flashcard, correct: bool) -> None:
        """Increment the global and per-card counters for ``card``."""
        bucket = self.per_card.setdefault(
            card.front, {"correct": 0, "incorrect": 0}
        )
        if correct:
            self.correct += 1
            bucket["correct"] += 1
        else:
            self.incorrect += 1
            bucket["incorrect"] += 1


def _normalize(answer: str) -> str:
    """Lowercase, collapse internal whitespace, strip leading/trailing spaces."""
    return " ".join(answer.strip().lower().split())


def is_correct(user_answer: str, expected: str) -> bool:
    """Return ``True`` when ``user_answer`` matches ``expected`` after
    case-insensitive whitespace-tolerant normalization.

    Exposed (rather than kept private) so the CLI test-suite can cover the
    comparison rules independently of the I/O loop.
    """
    return _normalize(user_answer) == _normalize(expected)


def run_session(
    quiz: QuizMode,
    *,
    input_fn: Callable[[str], str] = input,
    out: Optional[IO[str]] = None,
    use_color: Optional[bool] = None,
) -> SessionStats:
    """Drive ``quiz`` interactively until exhaustion or user exit.

    Args:
        quiz: The strategy that decides which card to serve next.
        input_fn: Callable that takes a prompt and returns the user's line.
            Defaults to the built-in :func:`input`; tests inject a stub.
        out: Stream to write prompts and feedback to. Defaults to ``stdout``
            via :func:`print`'s default behavior.
        use_color: Force-enable or force-disable ANSI colors. When ``None``
            (the default), auto-detects based on ``out``'s TTY status and
            the ``NO_COLOR`` environment variable.

    Returns:
        A :class:`SessionStats` instance reflecting the prompts the user
        actually answered. Cards skipped via exit/EOF/SIGINT are not
        counted.
    """
    color = colors_enabled(out) if use_color is None else use_color
    stats = SessionStats()

    _print(
        colorize(
            f"Starting quiz with {quiz.total} card(s). "
            "Type 'exit' (or press Ctrl+C) to quit.",
            CYAN,
            enabled=color,
        ),
        out,
    )
    _print(colorize("Answers are case-insensitive.", DIM, enabled=color), out)
    _print("", out)

    served = 0
    while True:
        card = quiz.next_card()
        if card is None:
            break
        served += 1
        _print(
            colorize(f"Q{served}: {card.front}", BOLD, enabled=color),
            out,
        )
        try:
            raw = input_fn("Your answer> ")
        except (EOFError, KeyboardInterrupt):
            _print("", out)
            _print(
                colorize("Session interrupted — exiting.", YELLOW, enabled=color),
                out,
            )
            break

        if _normalize(raw) in EXIT_COMMANDS:
            _print(
                colorize("Exiting quiz at user request.", YELLOW, enabled=color),
                out,
            )
            break

        correct = is_correct(raw, card.back)
        quiz.record_result(correct)
        stats.record(card, correct)

        if correct:
            _print(green("[OK] Correct!", enabled=color), out)
        else:
            _print(
                red(f"[X]  Incorrect. Expected: {card.back}", enabled=color),
                out,
            )
        _print("", out)

    return stats


def render_summary(
    stats: SessionStats,
    *,
    detailed: bool = False,
    use_color: bool = True,
) -> str:
    """Build the end-of-session summary string.

    When ``detailed`` is ``True``, appends a per-card breakdown listing how
    many times each card was answered correctly vs. incorrectly. This is
    what the ``--stats`` CLI flag toggles.
    """
    if stats.answered == 0:
        return colorize(
            "No questions answered — nothing to summarize.",
            YELLOW,
            enabled=use_color,
        )

    lines = [
        colorize("=== Session Summary ===", BOLD, enabled=use_color),
        f"Answered:  {stats.answered}",
        green(f"Correct:   {stats.correct}", enabled=use_color),
        red(f"Incorrect: {stats.incorrect}", enabled=use_color),
        f"Accuracy:  {stats.accuracy:.0%}",
    ]

    if detailed and stats.per_card:
        lines.append("")
        lines.append(
            colorize("Per-card breakdown:", BOLD, enabled=use_color)
        )
        for front, counts in stats.per_card.items():
            tag = (
                green("[OK]", enabled=use_color)
                if counts["incorrect"] == 0
                else red("[X] ", enabled=use_color)
            )
            lines.append(
                f"  {tag} {front} "
                f"(correct={counts['correct']}, "
                f"incorrect={counts['incorrect']})"
            )

    return "\n".join(lines)


def _print(message: str, out: Optional[IO[str]]) -> None:
    """Thin wrapper around :func:`print` that respects an optional stream.

    Centralizes the ``file=``-vs-default logic so the loop reads cleanly.
    """
    if out is None:
        print(message)
    else:
        print(message, file=out)
