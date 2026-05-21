#!/usr/bin/env bash
# Definition-of-Done check for FlashcardQuizzer.
# Runs pytest, black --check, and mypy. Exits non-zero on first failure.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${VIRTUAL_ENV:-}" && -f "venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

echo "==> [1/3] black --check ."
black --check .

echo "==> [2/3] mypy utils main.py"
mypy utils main.py

echo "==> [3/3] pytest"
pytest

echo "==> Definition of Done: PASS"
