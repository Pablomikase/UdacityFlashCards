"""Entry point for the FlashcardQuizzer CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from utils.data_loader import FlashcardDataError, load_flashcards
from utils.quiz_factory import QUIZ_MODES, create_quiz_mode


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--mode",
    type=click.Choice(QUIZ_MODES, case_sensitive=False),
    default="sequential",
    show_default=True,
    help="Order in which cards are presented during the quiz session.",
)
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    required=True,
    help=(
        "Path to the glossary JSON file. Accepts a bare array of "
        '{"front", "back"} cards or an object with a "cards" array.'
    ),
)
def main(mode: str, file_path: Path) -> None:
    """Run the FlashcardQuizzer quiz loop against a JSON glossary file."""
    try:
        cards = load_flashcards(file_path)
    except FlashcardDataError as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)

    quiz = create_quiz_mode(mode, cards)
    click.echo(f"Loaded {quiz.total} cards from {file_path}.")
    click.echo(f"Quiz mode: {mode.lower()}.")
    click.echo(
        "Quiz engine ready — interactive prompting will be wired up "
        "in the next iteration."
    )


if __name__ == "__main__":
    main()
