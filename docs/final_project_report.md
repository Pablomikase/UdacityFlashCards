# AI-Assisted Development Project Report

**Student Name:** Pablo Avila
**Project Title:** FlashcardQuizzer — Interactive CLI Flashcard Quiz with Strategy + Factory Patterns
**Date:** 2026-05-22

## Executive Summary

FlashcardQuizzer is a Python 3.9 CLI that turns a JSON glossary into an interactive quiz. The user runs `python main.py -m adaptive -f data/python_basics.json`; the program validates the deck and drives one of three card-ordering strategies until the deck is exhausted or the user types `exit`. Feedback is green/red ANSI, with an optional per-card breakdown.

The project was built almost entirely through AI collaboration with Claude. What made the collaboration productive was the upfront investment in two things: an **XML-based prompt format** stored in `docs/prompts_log.xml`, and a Claude *skill* configured at the start of the project to auto-capture every prompt to that file. Once the Definition of Done (pytest + flake8 + mypy + black + coverage ≥ 80%) and those triggers were wired up, each new phase landed in a single shot with the quality gates already enforced.

## Project Overview

### Problem Statement
Existing flashcard tools lock users into a GUI or force them to write code to add cards. FlashcardQuizzer targets developers who keep glossaries in version control: drop a JSON file into `data/`, and the CLI quizzes you. The three modes cover three intents — *cram in order*, *break memorization of the order*, and *focus on what I keep getting wrong*.

### Solution Approach
A thin orchestration layer (`main.py`) plus utility modules under `utils/`. The two design patterns live together in `utils/quiz_engine.py`:

- **Strategy Pattern** — `QuizMode` is an abstract base class with three concrete strategies. Each encapsulates one ordering policy behind the same `next_card()` / `record_result(correct)` interface, so the session loop is unaware of which policy is active.
- **Factory Pattern** — `create_quiz_mode(name, cards, *, rng=None)` maps a CLI mode string to the matching strategy. `main.py` never imports the concrete classes, so a new mode requires only a new subclass plus one dispatch entry.

Standard library only for production code; `pytest`, `flake8`, `mypy`, and `black` driving quality gates from a single `pyproject.toml`.

### Final Features
- [x] JSON glossary loader accepting both array and `{"cards": [...]}` shapes, with per-card validation and 1-based error indices
- [x] Three quiz modes wired through Strategy + Factory
- [x] Interactive loop with ANSI feedback, `--stats` breakdown, `--no-color` escape hatch
- [x] Graceful exit on `exit` / Ctrl+C / Ctrl+D / SIGINT during I/O — never a traceback
- [x] 108 tests at 97.77% branch coverage

## AI Collaboration Experience

### AI Tools Used
- [x] Claude (Claude Code CLI)

### Collaboration Workflow

My workflow centered on three habits that compounded:

1. **XML-structured prompts in `docs/prompts_log.xml`.** Every substantive request was written as an XML element with explicit `<role>`, `<task>`, `<context>`, `<requirements>`, `<constraints>`, and `<success_criteria>` children. This shape forces you to name the file paths, exception types, test categories, and success bar *before* the AI sees the request. For complex, multi-file requests this was the single highest-leverage habit of the project — see id="004" (data layer) and id="005" (quiz engine), where the XML structure essentially became the implementation spec. **For complex and structured prompts, XML is not a stylistic choice; it is the only way to keep the request unambiguous across half a dozen acceptance criteria.**

2. **Definition of Done + a Claude skill that auto-logs prompts.** Early in the project I configured a `prompt-logger` skill (under `.claude/skills/`) that appends each substantive prompt to the XML log, plus a `UserPromptSubmit` hook that nudged Claude to invoke it after every reply. Combined with `scripts/done_check.sh` (black + mypy + pytest) and a `.flake8` config aligned with `black`'s line length, the project had two automation rails — one for prompt hygiene, one for code quality. **Once those triggers were in place, the perceived velocity of code generation was the most impressive shift in the entire project.** Phases I would have estimated at half a day each (CLI scaffold, data layer, quiz engine, interactive loop, test alignment) each landed in a single Claude session, because every prompt arrived pre-structured and every output was immediately scored against the DoD.

3. **Review before merge.** Every AI-generated file was read top-to-bottom before staging. The most common modifications were tightening error paths (the AI tended to swallow `KeyboardInterrupt` while handling `EOFError`, or to emit "invalid JSON" without parser line/column) and consolidating module layout when the rubric pointed at a specific filename.

### Most Valuable AI Interactions

#### Example 1: Implementing Strategy + Factory in one pass
**Context:** Three interchangeable card-ordering strategies plus a name-based factory.
**AI Prompt:** XML-structured (`prompts_log.xml` id="005") with explicit `<test_categories>` enumerating every behavior to cover.
**AI Response:** A `QuizMode` ABC, three concrete strategies including an `AdaptiveMode` that prioritizes by miss count with original-index tiebreaks, and a `create_quiz_mode` factory with case-insensitive matching and an injectable RNG.
**Your Changes:** Made `UnknownQuizModeError` subclass `ValueError`; later consolidated `quiz_modes.py` and `quiz_factory.py` into a single `utils/quiz_engine.py` so the rubric inspector finds both patterns in one file.
**Outcome:** Both patterns implemented and fully tested in one session.

#### Example 2: Graceful exit across four signals
**Context:** The session loop had to handle `exit`/`quit`/`:q`, Ctrl+C, Ctrl+D, and SIGINT during I/O without ever showing a traceback.
**AI Prompt:** `prompts_log.xml` id="006" with each exit path named explicitly in `<success_criteria>`.
**Your Changes:** Added a `main()`-level `KeyboardInterrupt` belt-and-suspenders for SIGINT raised *outside* the loop.
**Outcome:** A loop that never produces a Python traceback under any tested exit condition.

### Challenges with AI Collaboration
The AI optimized for the demo path. Edge cases — empty card lists, JSON line/column in error messages, signal handling, non-TTY color auto-detection — all required explicit prompting. Once `<test_categories>` and `<error_handling_requirements>` became standard XML children, the gap closed quickly.

## Software Engineering Practices

### Code Quality Measures
- [x] `black` formatting (line length 88)
- [x] `flake8` clean (`.flake8` aligned with `black`)
- [x] `mypy` with `disallow_untyped_defs=True` for production code
- [x] Docstrings on every module and public function
- [x] Single-exception error surface per module (`FlashcardDataError`, `UnknownQuizModeError`)

### Testing Strategy
108 tests across 9 files: unit tests per module plus `tests/test_integration.py` driving the full pipeline (loader → factory → session loop) on a tmpfile glossary with a scripted `input_fn`. Branch coverage is **97.77%** under `pytest --cov=utils --cov-branch`. I did not use strict TDD, but prompting with `<test_categories>` lists produced near-TDD output: implementation and tests landed together in each phase.

### Design Patterns Used
- **Strategy Pattern** — `QuizMode` ABC plus `SequentialMode`, `RandomMode`, `AdaptiveMode` in `utils/quiz_engine.py`. The session loop holds a `QuizMode` reference and calls `next_card()` / `record_result()` polymorphically — exactly the decoupling the pattern is named for.
- **Factory Pattern** — `create_quiz_mode(name, cards, *, rng=None)` in the same module resolves a CLI mode name to the matching strategy. `main.py` never imports the concrete classes.

Together these patterns gave the project its most important property: **the session loop is closed for modification but open for extension.** That is the textbook benefit of Strategy + Factory, and the test suite proves it — `test_quiz_modes.py` and `test_quiz_factory.py` exercise the pattern boundary without ever touching the loop. Adding a spaced-repetition mode would be one new `QuizMode` subclass plus one factory dispatch line; zero changes to the loop, zero changes to `main.py`.

## Technical Challenges and Solutions

### Challenge 1: Rubric-required filename mismatch
**Problem:** Strategy + Factory originally lived in two files; the rubric mandated inspection of `quiz_engine.py`.
**Solution:** Consolidated into `utils/quiz_engine.py`, deleted the two old files, updated four test files and `main.py`. 108 tests stayed green.
**Lessons Learned:** When a rubric names a file path, treat it as a hard requirement.

### Challenge 2: 79 flake8 violations on legacy starter files
**Problem:** Starter modules had W293 whitespace, W292 missing-EOL, and F401 unused-import noise across seven files.
**Solution:** Added `.flake8` with `max-line-length=88` matching `black`, then rewrote the offending files cleanly.
**Lessons Learned:** Align linter config with formatter config from day one.

## Code Quality Analysis

### Metrics
- Lines of Python: **2,008** (production + tests)
- Test coverage: **97.77%** branch
- Tests: **108 passing**
- Linting: **flake8 clean**, `black --check` clean, `mypy` clean

### Self-Assessment
- **Code Readability:** 5 — short modules, named exceptions, every public function has a docstring with a *why*.
- **Code Maintainability:** 5 — patterns enforce extension points; `main.py` is pure orchestration.
- **Test Quality:** 5 — branch coverage 97.77%, integration test exercises the full path.
- **Documentation:** 4 — `docs/ai_edit_log.md` and `docs/prompts_log.xml` provide a full collaboration history.

## Learning Outcomes

**Technical:** Strategy and Factory patterns in practice, argparse-based CLI design, branch coverage as a stronger signal than line coverage, and `dataclasses(frozen=True)` for immutable value objects.

**AI Collaboration:** XML-structured prompts are the right shape for complex requests — they force the requester to name files, errors, and success criteria before the AI is allowed to guess. After configuring the Definition of Done and the `prompt-logger` skill triggers, AI-assisted code generation became startlingly fast: each phase was one prompt, one review, one commit.

**Software Engineering:** A Definition of Done that fails the build on a single regression is worth more than any code-review checklist.

## Reflection

**What Worked Well:** XML prompts in `docs/prompts_log.xml`; the `prompt-logger` skill that captured them automatically; consolidating Strategy + Factory into one inspectable file; 97.77% branch coverage.

**What Could Be Improved:** Pinning file layout in the prompt before code is generated would have avoided the `quiz_modes.py` / `quiz_factory.py` → `quiz_engine.py` migration mid-project.

**Future Enhancements:** A spaced-repetition `QuizMode` subclass, session persistence to JSON, and a TUI front-end reusing `run_session()` unchanged.

## Conclusion

FlashcardQuizzer is a small project, but it landed three lessons that scale. First, **complex prompts belong in XML** — anything with more than three acceptance criteria becomes ambiguous in prose. Second, **automating the Definition of Done and the prompt log up front makes AI-generated code feel fast**, because every output is immediately scored against the quality bar. Third, **design patterns earn their keep when the file layout matches them** — Strategy and Factory in one `quiz_engine.py` made the architecture legible at first glance.

## Appendices

### Appendix A: AI Interaction Log
See `docs/ai_edit_log.md` (7 entries) and `docs/prompts_log.xml` (7 XML-structured prompts).

### Appendix B: Code Statistics
2,008 lines of Python across 18 files; 108 tests at 97.77% branch coverage; `htmlcov/index.html` generated by `pytest --cov=utils --cov-branch --cov-report=html`.

### Appendix C: Additional Resources
- `docs/design_patterns.md` — pattern reference used during implementation
- `docs/project_rubric.md` — graded criteria checklist
- `ai_guidance/prompting_best_practices.md` — XML-prompt template guide
