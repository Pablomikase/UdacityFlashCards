"""ANSI color helpers for terminal output.

Provides a tiny palette of ANSI escape codes plus a :func:`colorize` helper
that becomes a no-op when colors are disabled (non-TTY output, ``NO_COLOR``
in the environment, or an explicit ``enabled=False`` flag).

This module is intentionally dependency-free so the CLI does not need
``colorama`` or similar on POSIX terminals.
"""

from __future__ import annotations

import os
import sys
from typing import IO, Optional

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def colors_enabled(stream: Optional[IO[str]] = None) -> bool:
    """Return ``True`` when ANSI escape codes should be written to ``stream``.

    Honors the ``NO_COLOR`` convention (https://no-color.org) and disables
    colors when the target stream is not a TTY (e.g. when output is being
    piped or captured by a test).
    """
    if "NO_COLOR" in os.environ:
        return False
    target = stream if stream is not None else sys.stdout
    isatty = getattr(target, "isatty", None)
    return bool(isatty and isatty())


def colorize(text: str, color: str, *, enabled: bool = True) -> str:
    """Wrap ``text`` in ANSI codes, or return it unchanged when disabled."""
    if not enabled or not color:
        return text
    return f"{color}{text}{RESET}"


def green(text: str, *, enabled: bool = True) -> str:
    """Render ``text`` in green (used for correct answers)."""
    return colorize(text, GREEN, enabled=enabled)


def red(text: str, *, enabled: bool = True) -> str:
    """Render ``text`` in red (used for incorrect answers)."""
    return colorize(text, RED, enabled=enabled)
