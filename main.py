"""Entry point for the FlashcardQuizzer CLI.

Wires together argument parsing, glossary loading, quiz-mode construction
and the interactive session loop. Keeps its own surface small: the heavy
lifting lives in ``utils/`` so this module remains a thin orchestration
layer that is easy to read top-to-bottom.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from utils.colors import YELLOW, colorize, colors_enabled
from utils.data_loader import FlashcardDataError, load_flashcards
from utils.quiz_engine import (
    QUIZ_MODES,
    UnknownQuizModeError,
    create_quiz_mode,
)
from utils.quiz_session import render_summary, run_session


def build_parser() -> argparse.ArgumentParser:
    """Configure the CLI argument parser.

    Returning the parser (instead of parsing inline) keeps the wiring
    testable: tests can call ``build_parser().parse_args([...])`` without
    spawning a subprocess.
    """
    parser = argparse.ArgumentParser(
        prog="flashcard-quizzer",
        description=(
            "Interactive flashcard quiz over a JSON glossary file. "
            "Type 'exit' or press Ctrl+C at any prompt to quit gracefully."
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="file_path",
        type=Path,
        required=True,
        metavar="PATH",
        help=(
            "Path to the glossary JSON file. Accepts a bare array of "
            "{front, back} cards or an object with a 'cards' array."
        ),
    )
    parser.add_argument(
        "-m",
        "--mode",
        dest="mode",
        choices=QUIZ_MODES,
        default="sequential",
        help="Card ordering strategy (default: %(default)s).",
    )
    parser.add_argument(
        "--stats",
        dest="show_detailed_stats",
        action="store_true",
        help=(
            "Print a detailed per-card breakdown in the end-of-session "
            "summary (totals are always shown)."
        ),
    )
    parser.add_argument(
        "--no-color",
        dest="color",
        action="store_false",
        default=True,
        help="Disable ANSI color output (also honored via NO_COLOR env var).",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the quiz session described by ``args``; return the exit code.

    Split out from :func:`main` so tests can drive it with a hand-built
    ``Namespace`` and assert on the returned status without monkeypatching
    ``sys.argv``.
    """
    use_color = args.color and colors_enabled()

    try:
        cards = load_flashcards(args.file_path)
    except FlashcardDataError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    try:
        quiz = create_quiz_mode(args.mode, cards)
    except UnknownQuizModeError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    stats = run_session(quiz, use_color=use_color)
    print()
    print(
        render_summary(
            stats,
            detailed=args.show_detailed_stats,
            use_color=use_color,
        )
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point; returns a process exit code rather than calling
    :func:`sys.exit` so it composes cleanly with tests and other tooling.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return run(args)
    except KeyboardInterrupt:
        # Safety net for SIGINT raised outside the session loop (e.g.
        # during file I/O). The loop itself catches Ctrl+C and exits
        # cleanly, but we never want a raw traceback to reach the user.
        use_color = args.color and colors_enabled(sys.stderr)
        print(
            colorize("\nQuiz aborted.", YELLOW, enabled=use_color),
            file=sys.stderr,
        )
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # Belt-and-suspenders: should never reach here because main()
        # already catches KeyboardInterrupt, but guarantees a quiet exit.
        sys.exit(0)
