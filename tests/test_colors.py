"""Tests for utils.colors (ANSI helpers)."""

from __future__ import annotations

import io

import pytest

from utils import colors


def test_colorize_wraps_in_escape_codes_when_enabled():
    out = colors.colorize("hi", colors.GREEN, enabled=True)
    assert out == f"{colors.GREEN}hi{colors.RESET}"


def test_colorize_is_noop_when_disabled():
    assert colors.colorize("hi", colors.GREEN, enabled=False) == "hi"


def test_green_and_red_use_expected_codes():
    assert colors.green("ok") == f"{colors.GREEN}ok{colors.RESET}"
    assert colors.red("bad") == f"{colors.RED}bad{colors.RESET}"


def test_colors_disabled_for_non_tty_stream():
    # io.StringIO is not a TTY, so auto-detection must return False.
    assert colors.colors_enabled(io.StringIO()) is False


def test_no_color_env_var_disables_colors(monkeypatch):
    class FakeTTY:
        def isatty(self) -> bool:
            return True

    monkeypatch.setenv("NO_COLOR", "1")
    assert colors.colors_enabled(FakeTTY()) is False


def test_colors_enabled_for_tty_when_no_color_unset(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)

    class FakeTTY:
        def isatty(self) -> bool:
            return True

    assert colors.colors_enabled(FakeTTY()) is True


def test_colorize_with_empty_color_is_passthrough():
    # Defensive: passing an empty color string should not produce stray
    # escape sequences.
    assert colors.colorize("x", "", enabled=True) == "x"
