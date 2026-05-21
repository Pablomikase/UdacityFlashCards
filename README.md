# FlashcardQuizzer

An interactive Python 3.9 command-line flashcard quiz. Point it at a JSON glossary, pick one of three card-ordering strategies, and study at the terminal with green/red ANSI feedback and an end-of-session summary.

The application is structured around two design patterns that live together in `utils/quiz_engine.py`:

- **Strategy Pattern** — `QuizMode` abstract base class with three interchangeable concrete strategies (`SequentialMode`, `RandomMode`, `AdaptiveMode`).
- **Factory Pattern** — `create_quiz_mode(name, cards, *, rng=None)` resolves a CLI mode name to the matching strategy, so `main.py` never imports the concrete classes.

## Quick Start

```bash
# Clone and enter the project
git clone https://github.com/Pablomikase/UdacityFlashCards.git
cd UdacityFlashCards

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the rubric-spec command (adaptive mode)
python main.py -m adaptive -f data/python_basics.json
```

Type your answer at each prompt. Type `exit`, `quit`, or `:q` (or press Ctrl+C / Ctrl+D) to leave the session early — you will still get the summary.

## Features

- **Three quiz modes** wired through Strategy + Factory:
  - `sequential` — cards in file order (default).
  - `random` — every card once, shuffled. Accepts an injectable `random.Random` for deterministic tests.
  - `adaptive` — every card once, then re-serves missed cards prioritized by miss count until each card has been answered correctly at least once.
- **Two glossary shapes accepted** — bare JSON array of `{front, back}` objects, or an object wrapper `{"cards": [...]}`. See `data/glossary.json` and `data/glossary_object.json`.
- **Friendly errors instead of tracebacks.** Missing file, unreadable file, malformed JSON (with line/column), wrong top-level shape, or per-card validation failures all produce a single line on `stderr` and exit code 1.
- **ANSI feedback** — correct answers in green, incorrect in red. Auto-disabled on non-TTY streams and when `NO_COLOR` is set. Forceable off with `--no-color`.
- **`--stats` per-card breakdown** — appended to the summary, listing how many times each card was answered correctly vs. incorrectly.
- **Graceful exit on every signal** — `exit` / `quit` / `:q`, Ctrl+C, Ctrl+D, and SIGINT raised during I/O all exit cleanly with a summary; no Python traceback ever reaches the user.

## CLI Reference

```
python main.py -f PATH [-m {sequential,random,adaptive}] [--stats] [--no-color]
```

| Flag | Description | Default |
|---|---|---|
| `-f`, `--file` | Path to a JSON glossary file (required). | — |
| `-m`, `--mode` | Card ordering strategy: `sequential`, `random`, or `adaptive`. | `sequential` |
| `--stats` | Append a per-card correctness breakdown to the end-of-session summary. | off |
| `--no-color` | Disable ANSI color output (also honored via `NO_COLOR`). | colors on |

### Glossary JSON format

Array form (`data/glossary.json`, `data/python_basics.json`):

```json
[
  { "front": "What keyword defines a function in Python?", "back": "def" },
  { "front": "Which built-in returns the length of a sequence?", "back": "len" }
]
```

Object form (`data/glossary_object.json`):

```json
{
  "title": "Python Basics",
  "cards": [
    { "front": "What keyword defines a function in Python?", "back": "def" }
  ]
}
```

Both `front` and `back` must be non-empty strings; an empty card list is rejected.

## Project Structure

```
.
├── main.py                          # argparse CLI entry point (orchestration only)
├── utils/
│   ├── __init__.py
│   ├── colors.py                    # ANSI helpers + NO_COLOR / non-TTY auto-detect
│   ├── data_loader.py               # load_flashcards + FlashcardDataError
│   ├── quiz_engine.py               # Strategy (QuizMode + 3 strategies) + Factory
│   ├── quiz_session.py              # Interactive loop, SessionStats, render_summary
│   ├── file_handler.py              # (starter utility, retained for course continuity)
│   └── task_manager.py              # (starter utility, retained for course continuity)
├── tests/                           # 108 tests, 97.77% branch coverage
│   ├── test_flashcard_loader.py     # rubric-named loader tests
│   ├── test_quiz_modes.py           # rubric-named Strategy tests
│   ├── test_quiz_factory.py         # Factory dispatch + rng injection
│   ├── test_quiz_session.py         # session loop + stats
│   ├── test_main_cli.py             # argparse + main() integration
│   ├── test_integration.py          # full pipeline on a tmpfile glossary
│   ├── test_colors.py
│   ├── test_file_handler.py
│   └── test_task_manager.py
├── data/
│   ├── python_basics.json           # 10 Python-basics cards (array form)
│   ├── glossary.json                # OOP glossary (array form)
│   └── glossary_object.json         # Same content in object-wrapper form
├── docs/
│   ├── final_project_report.md      # Final course report
│   ├── ai_edit_log.md               # 7 detailed AI-collaboration entries
│   ├── prompts_log.xml              # 7 XML-structured prompts (one per phase)
│   ├── design_patterns.md           # Pattern reference
│   ├── project_rubric.md            # Graded criteria
│   └── report_template.md           # Empty template (course-provided)
├── ai_guidance/                     # XML prompt-template + review checklist
├── .claude/                         # Claude Code config: CLAUDE.md, skills, MCP
├── scripts/done_check.sh            # Runs black + mypy + pytest (Definition of Done)
├── pyproject.toml                   # pytest, black, mypy config
├── .flake8                          # flake8 config (max-line-length=88, aligned with black)
├── .editorconfig
├── requirements.txt
└── README.md
```

## Quality Gates

The project's Definition of Done is enforced by four tools driven from `pyproject.toml` and `.flake8`:

```bash
black --check .                      # formatting
flake8 .                             # linting (max-line-length=88, matches black)
mypy utils main.py                   # static typing (disallow_untyped_defs=True for production)
pytest                               # 108 tests, --cov-fail-under=80, branch coverage
```

A single-command sweep is available:

```bash
./scripts/done_check.sh
```

Current metrics:

- **Tests:** 108 passing
- **Branch coverage:** 97.77% (target: ≥ 80%)
- **flake8:** clean
- **black --check:** clean
- **mypy:** clean

To regenerate the HTML coverage report:

```bash
pytest --cov=utils --cov-branch --cov-report=html
open htmlcov/index.html              # macOS; use xdg-open on Linux
```

## Extending the Quiz Engine

Adding a fourth mode (e.g. spaced-repetition) is intentionally cheap thanks to the Strategy + Factory split:

1. Add a new `QuizMode` subclass to `utils/quiz_engine.py` implementing `next_card()` and, if the strategy is adaptive, overriding `record_result(correct)`.
2. Add one dispatch line to `create_quiz_mode()` and one entry to the `QUIZ_MODES` tuple.
3. Add unit tests that exercise the new strategy through the public interface.

`main.py` and `utils/quiz_session.py` do not change.

## AI Collaboration

This project was built almost entirely through AI collaboration with Claude (via the Claude Code CLI). The full history is in:

- `docs/ai_edit_log.md` — seven narrative entries (context, prompt, AI response, changes, reasoning, outcome, lessons).
- `docs/prompts_log.xml` — the same seven prompts in XML form, with explicit `<role>`, `<task>`, `<context>`, `<requirements>`, `<constraints>`, and `<success_criteria>` children. Auto-captured by a `prompt-logger` skill configured in `.claude/skills/`.

See `docs/final_project_report.md` for the full reflection on the workflow.

## Built With

- [Python 3.9](https://www.python.org/)
- [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/)
- [black](https://black.readthedocs.io/), [flake8](https://flake8.pycqa.org/), [mypy](https://mypy.readthedocs.io/)
- [Claude Code](https://claude.com/claude-code) — AI pair-programming CLI

## License

[License](LICENSE.txt)
