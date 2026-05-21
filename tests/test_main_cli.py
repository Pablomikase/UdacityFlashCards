"""Tests for the argparse-based CLI in ``main.py``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

import main
from utils.quiz_session import SessionStats


# --- build_parser -----------------------------------------------------------


def test_parser_accepts_short_flags(tmp_path: Path):
    fake_file = tmp_path / "g.json"
    fake_file.write_text("[]", encoding="utf-8")  # content irrelevant for parsing

    args = main.build_parser().parse_args(
        ["-f", str(fake_file), "-m", "random", "--stats"]
    )
    assert args.file_path == fake_file
    assert args.mode == "random"
    assert args.show_detailed_stats is True
    assert args.color is True  # default


def test_parser_accepts_long_flags(tmp_path: Path):
    fake_file = tmp_path / "g.json"
    fake_file.write_text("[]", encoding="utf-8")

    args = main.build_parser().parse_args(
        ["--file", str(fake_file), "--mode", "adaptive", "--no-color"]
    )
    assert args.mode == "adaptive"
    assert args.color is False
    assert args.show_detailed_stats is False


def test_parser_requires_file_flag():
    with pytest.raises(SystemExit):
        main.build_parser().parse_args(["-m", "sequential"])


def test_parser_rejects_unknown_mode(tmp_path: Path):
    fake_file = tmp_path / "g.json"
    fake_file.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit):
        main.build_parser().parse_args(["-f", str(fake_file), "-m", "bogus"])


def test_parser_defaults(tmp_path: Path):
    fake_file = tmp_path / "g.json"
    fake_file.write_text("[]", encoding="utf-8")
    args = main.build_parser().parse_args(["-f", str(fake_file)])
    assert args.mode == "sequential"
    assert args.show_detailed_stats is False
    assert args.color is True


# --- main() integration -----------------------------------------------------


def _write_glossary(path: Path, pairs: List[tuple]) -> None:
    payload = [{"front": f, "back": b} for f, b in pairs]
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_main_returns_zero_on_successful_session(
    tmp_path: Path, monkeypatch, capsys
):
    glossary = tmp_path / "g.json"
    _write_glossary(glossary, [("Q1", "A1"), ("Q2", "A2")])

    fake_stats = SessionStats()
    # Pretend the user answered everything correctly.
    from utils.data_loader import Flashcard

    fake_stats.record(Flashcard("Q1", "A1"), True)
    fake_stats.record(Flashcard("Q2", "A2"), True)

    monkeypatch.setattr(main, "run_session", lambda quiz, **kw: fake_stats)
    rc = main.main(["-f", str(glossary), "-m", "sequential"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Session Summary" in captured.out
    assert "Accuracy:  100%" in captured.out


def test_main_passes_stats_flag_into_summary(tmp_path: Path, monkeypatch, capsys):
    glossary = tmp_path / "g.json"
    _write_glossary(glossary, [("Q1", "A1")])

    from utils.data_loader import Flashcard

    fake_stats = SessionStats()
    fake_stats.record(Flashcard("Q1", "A1"), False)

    monkeypatch.setattr(main, "run_session", lambda quiz, **kw: fake_stats)
    rc = main.main(["-f", str(glossary), "--stats"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Per-card breakdown" in captured.out


def test_main_reports_data_error_on_missing_file(tmp_path: Path, capsys):
    missing = tmp_path / "nope.json"
    rc = main.main(["-f", str(missing)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "not found" in captured.err.lower() or "no such" in captured.err.lower()


def test_main_reports_data_error_on_malformed_json(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json {", encoding="utf-8")
    rc = main.main(["-f", str(bad)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_main_swallows_keyboard_interrupt(tmp_path: Path, monkeypatch, capsys):
    glossary = tmp_path / "g.json"
    _write_glossary(glossary, [("Q1", "A1")])

    def raising_run(_args):
        raise KeyboardInterrupt

    monkeypatch.setattr(main, "run", raising_run)
    rc = main.main(["-f", str(glossary)])
    assert rc == 0  # graceful exit, no traceback
    captured = capsys.readouterr()
    assert "Quiz aborted" in captured.err
