# AI Edit Log

**Instructions:** Use this document to track all your interactions with AI assistants during the project. This log will help you reflect on your AI collaboration process and demonstrate your learning journey.

Each entry below mirrors a prompt captured in `docs/prompts_log.xml` and refines it into a course-style edit-log entry: context, exact prompt, the AI's response, what I changed, why, and what I learned.

## How to Use This Log

For each AI interaction, create a new entry with the following structure:

### Entry Template
```
## [Date] - [Brief Description]

**Context:** What were you trying to accomplish?
**AI Tool Used:** Claude/ChatGPT/Copilot/etc.
**Prompt/Request:** What exactly did you ask the AI?
**AI Response:** Summary of what the AI generated (don't copy entire code blocks)
**Changes Made:** What modifications did you make to the AI's suggestions?
**Reasoning:** Why did you make those changes?
**Outcome:** What was the final result?
**Lessons Learned:** What did you learn from this interaction?
```

---

## Your Log Entries

### 2026-05-21 - Bootstrap the Python virtual environment

**Context:** I needed a clean, isolated Python environment for FlashcardQuizzer so that pinned dependencies in `requirements.txt` would not collide with system-wide packages on macOS.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Bootstrap the isolated Python working environment for the FlashcardQuizzer project and install every dependency declared in requirements.txt." (See prompts_log.xml id="001".)

**AI Response:** Claude produced a four-command sequence: `python3 -m venv venv`, `source venv/bin/activate`, `pip install --upgrade pip`, and `pip install -r requirements.txt`, plus explicit success criteria (venv directory exists, pip is upgraded, every package installs cleanly).

**Changes Made:**
- Pinned the prompt to my actual interpreter (system Python 3.9.5) instead of accepting a vague "use Python 3.x".
- Wrote the success criteria into the prompt itself so the AI couldn't declare victory while skipping `--upgrade pip`.

**Reasoning:** Locking the runtime version up front avoids the classic "works on my machine" trap, and embedding success criteria turns the prompt into a self-checking spec.

**Outcome:** A working `./venv` with all dependencies installed, ready for pytest/black/flake8/mypy.

**Lessons Learned:** Treat environment setup as a first-class prompt with explicit success criteria — it pays off every time the project is cloned on a new machine.

---

### 2026-05-21 - Define a three-gate Definition of Done

**Context:** I wanted the project to fail loudly the moment tests, formatting, or type checks regressed — not at code-review time.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Wire up the project's Definition of Done so completion is gated by three automated checks: test execution, code formatting, and static type checking." (See prompts_log.xml id="002".)

**AI Response:** Claude proposed a single `pyproject.toml` driving pytest (with `--cov-fail-under=80`), black (`line-length=88`, `py39` target), and mypy (`disallow_untyped_defs=True` for production code, relaxed for tests).

**Changes Made:**
- Asked the AI to also exclude `venv/`, `build/`, `dist/`, and `htmlcov/` from black and mypy explicitly, instead of relying on defaults.
- Added `--cov-branch` to pytest because the original recommendation only measured line coverage.

**Reasoning:** Branch coverage catches conditionals the AI's defaults would have left untested; explicit excludes prevent the tools from wandering into the virtualenv during CI.

**Outcome:** A single `pyproject.toml` that drives all three quality gates, and a coverage report that started failing realistically (~60%) before I had written more tests — exactly the early warning I wanted.

**Lessons Learned:** When configuring quality tools, always specify exclusions explicitly. "Smart defaults" diverge between local and CI environments more often than they agree.

---

### 2026-05-21 - Replace the demo `main.py` with a real CLI scaffold

**Context:** The starter `main.py` was a TaskManager demo. I needed it to become the real CLI entry point so `python main.py --help` would print every flag and `python main.py --mode sequential --file data/glossary.json` would actually load the glossary.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Refactor main.py into a CLI scaffold so `python main.py --help` lists every available flag and `python main.py --mode sequential --file data/glossary.json` loads the glossary without crashing." (See prompts_log.xml id="003".)

**AI Response:** Claude produced a click-based CLI with `--file`, `--mode` (choice of sequential/random/adaptive, default sequential), and explicit help text, plus validation that the JSON file is a non-empty array of `{front, back}` objects.

**Changes Made:**
- Asked for "not yet implemented" placeholder text where the real quiz loop would later live, so the scaffold could ship before the engine existed.
- Rejected the AI's first cut, which silently accepted empty card lists; insisted on a hard error.

**Reasoning:** A CLI scaffold that loads invalid input without complaint is worse than one that crashes — the loud failure is what catches bad files in the first day of testing.

**Outcome:** A passing `--help`, friendly errors for missing or malformed files, and a clean handoff point for the next phase. Later replaced with argparse in id="006", but the contract held.

**Lessons Learned:** Even disposable scaffolds need real validation; "we'll harden it later" leaks bugs into the next phase that are much harder to debug.

---

### 2026-05-21 - Build the data ingestion layer (`utils/data_loader.py`)

**Context:** I needed a reusable loader that could accept both the bare-array and the `{"cards": [...]}` glossary formats, validate every card, and report errors as friendly single-line messages instead of Python tracebacks.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Build a data-loading subsystem that reads a JSON glossary file, accepts two structural shapes, validates every card, and surfaces any failure as a user-friendly message instead of a Python traceback." (See prompts_log.xml id="004".)

**AI Response:** Claude generated `utils/data_loader.py` with a `Flashcard` frozen dataclass, a `FlashcardDataError` exception, and a `load_flashcards()` function that auto-detects array vs object format, validates non-empty string fields, and includes the 1-based index in per-card errors.

**Changes Made:**
- Added the requirement that JSON parse errors must include `line` and `column` from the parser — the AI's first draft swallowed the location.
- Insisted that `main.py` catch the loader exception and print `Error: <message>` to stderr with exit code 1, never letting the traceback escape.

**Reasoning:** A loader that tells you "invalid JSON" without saying where wastes the user's first ten minutes. Surfacing the parser's line/column is a one-line fix that pays for itself every time the file is hand-edited.

**Outcome:** Both `data/glossary.json` (array) and `data/glossary_object.json` (object wrapper) load cleanly; malformed input always produces a single friendly line on stderr; per-card errors point at the right card by index.

**Lessons Learned:** When prompting for an error path, demand specifics ("include line and column", "1-based index", "stderr + exit 1") rather than asking for "good error messages" — the latter gets you generic strings.

---

### 2026-05-21 - Implement the quiz engine using Strategy + Factory

**Context:** The rubric requires both the Strategy and Factory patterns. I needed three interchangeable card-ordering strategies and a way for `main.py` to pick one by name without importing the concrete classes.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Implement the quiz engine using the Strategy Pattern, exposing three interchangeable ordering strategies, and select the active strategy at runtime through a Factory Pattern driven by the existing --mode CLI flag." (See prompts_log.xml id="005".)

**AI Response:** Claude produced a `QuizMode` ABC with `next_card()` and an overridable `record_result(correct)` hook; concrete `SequentialMode`, `RandomMode` (injectable `random.Random` for determinism), and `AdaptiveMode` (re-serves missed cards by miss count, ties broken by original index); and a `create_quiz_mode(name, cards, *, rng=None)` factory with case-insensitive whitespace-tolerant matching.

**Changes Made:**
- Initially Claude split the patterns across `utils/quiz_modes.py` and `utils/quiz_factory.py`. Later I consolidated both into a single `utils/quiz_engine.py` because the rubric explicitly says "checked by inspecting `quiz_engine.py`" — having the patterns living in one inspectable file makes the grading path frictionless.
- Forced the factory's `UnknownQuizModeError` to subclass `ValueError` so callers only need one catch.

**Reasoning:** Subclassing `ValueError` keeps the factory ergonomic for code that already catches the standard exception; consolidating into `quiz_engine.py` aligns with the rubric and removes the temptation to add re-export shims later.

**Outcome:** `python main.py -m adaptive -f data/python_basics.json` (and the sequential/random variants) runs cleanly; `main.py` no longer branches on the mode string; tests cover all three strategies plus the factory's case-insensitive lookup, rng injection, and unknown-mode behavior.

**Lessons Learned:** Patterns are easier to grade and to extend when they live in a single, clearly named module. If a rubric points at a file path, treat that path as a hard requirement — not a suggestion.

---

### 2026-05-21 - Build the interactive CLI session loop with colors and graceful exit

**Context:** The CLI needed an interactive loop that drives the strategies, colors feedback green/red, accumulates stats, and never lets a traceback escape — not on Ctrl+C, not on Ctrl+D, not on "exit".

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Implement the interactive CLI layer that drives the existing QuizMode strategies, replacing the placeholder click-based entry point with an argparse-driven flow that supports colored feedback and graceful exit handling." (See prompts_log.xml id="006".)

**AI Response:** Claude built `utils/colors.py` (ANSI helpers with `NO_COLOR` + non-TTY auto-detect), `utils/quiz_session.py` (the loop + `SessionStats` accumulator + `render_summary`), and rewrote `main.py` around argparse with `-f`, `-m`, `--stats`, and `--no-color` flags.

**Changes Made:**
- The AI's first draft swallowed `EOFError` but not `KeyboardInterrupt`. I made both produce the same one-line "Session interrupted — exiting." message and broke out of the loop with stats preserved.
- Added a defensive `main()`-level `KeyboardInterrupt` handler for SIGINT raised outside the loop (e.g. during file I/O) so the user never sees a raw traceback even on unusual paths.

**Reasoning:** Users will hit Ctrl+C mid-question more often than EOF; pretending only one matters is a UX bug. Belt-and-suspenders on the outer handler costs four lines and prevents an embarrassing traceback in demo mode.

**Outcome:** Typing `exit`, sending Ctrl+C, sending Ctrl+D, or finishing the deck all produce a clean summary with exit code 0; `--stats` adds the per-card breakdown; colors auto-disable on non-TTY streams and when `NO_COLOR` is set.

**Lessons Learned:** Graceful-exit handling needs to be specified path-by-path in the prompt. "Handle Ctrl+C gracefully" is too vague — Ctrl+C, Ctrl+D, the `exit`/`quit`/`:q` words, and SIGINT during I/O each need a named outcome.

---

### 2026-05-21 - Align the pytest suite with the rubric's required names

**Context:** My suite already had high coverage, but the rubric mandates specific filenames and function names (`test_flashcard_loader.py::test_load_valid_flashcards_array`, `test_quiz_modes.py::test_quiz_mode_factory`, `test_integration.py::test_full_session`, etc.). I needed the names to match verbatim without losing the existing tests.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Reorganize the existing tests so the rubric-required filenames and test functions exist verbatim, and confirm the full suite still passes `pytest --cov=. --cov-report=html` above the 80% threshold." (See prompts_log.xml id="007".)

**AI Response:** Claude renamed `test_data_loader.py` to `test_flashcard_loader.py`, added the three rubric-named loader tests at the top of the file, added `test_quiz_mode_factory` and `test_adaptive_mode_behavior` to `test_quiz_modes.py`, and created `test_integration.py::test_full_session` that drives `run_session` with a scripted `input_fn` over a 3-card glossary on `tmp_path`.

**Changes Made:**
- Made the integration test assert on `stats.correct`, `stats.incorrect`, `stats.accuracy`, `stats.per_card`, *and* the rendered summary string — not just totals — because per-card stats are the whole point of `--stats`.
- Kept the original test files alongside the rubric-named ones so coverage didn't regress; the rubric names are now a strict superset.

**Reasoning:** Renaming-and-replacing would have dropped ~30 existing tests; renaming-and-augmenting kept coverage at 97.80% while satisfying the rubric's literal name match.

**Outcome:** All six rubric-named tests resolve and pass; the full suite is 108 passed at 97.80% branch coverage; `htmlcov/index.html` regenerated.

**Lessons Learned:** When a rubric mandates specific names, satisfy them as additions, not replacements. Coverage you already have is worth more than tidy file names.

---

## Tips for Effective AI Collaboration

### 1. Be Specific in Your Requests
- Don't: "Write a function."
- Do: "Write a function that validates email addresses using regex, returns a boolean, and includes proper error handling."

### 2. Provide Context
- Include relevant code snippets
- Explain the larger goal
- Mention any constraints or requirements

### 3. Review and Understand
- Never copy AI code without understanding it
- Ask for explanations of complex logic
- Test the code before accepting it

### 4. Iterate and Refine
- Use follow-up questions to improve the code
- Ask for alternative implementations
- Request code reviews and suggestions

### 5. Document Your Process
- Keep detailed notes in this log
- Explain your decision-making process
- Track what works and what doesn't

## Reflection Questions

1. **What types of tasks did AI help with most effectively?**
   Generating scaffolds — argparse parsers, dataclass shells, ABC + concrete-subclass skeletons — and producing exhaustive test enumerations from a short spec. Anywhere the work is "lots of small, mostly-mechanical pieces that have to be consistent", the AI was net positive.

2. **Where did you need to make the most modifications to AI suggestions?**
   Error-path UX. The AI's defaults always swallowed too much (e.g. catching `EOFError` but not `KeyboardInterrupt`, or reporting "invalid JSON" without the line/column). Every error path needed explicit specification.

3. **What patterns did you notice in AI strengths and weaknesses?**
   Strength: well-typed, well-documented happy-path code. Weakness: defensive coverage of edge cases, especially user-driven exit paths and validation messages. The AI optimizes for the demo, not the post-demo support tickets.

4. **How did your prompting technique improve over time?**
   I moved from "build X" to "build X with these explicit success criteria", and I started embedding the test categories I wanted into the prompt itself (see prompts_log.xml id="004" and id="005"). That turned the AI's output into a self-checking spec.

5. **What would you do differently in future AI collaborations?**
   Pin the file layout in the prompt before any code is generated. I split Strategy and Factory across two files initially and had to consolidate later because the rubric pointed at `quiz_engine.py` specifically.

## Summary Statistics

- **Total AI interactions logged in `prompts_log.xml`:** 7 (mirrored as 7 entries above)
- **Lines of AI-generated code used:** ~600 across `utils/` and `tests/`
- **Lines of AI-generated code modified:** ~120 (error paths, file consolidation, validation tightening)
- **Most helpful AI interaction:** id="005" — implementing Strategy + Factory in one pass with deterministic-rng injection ready for testing.
- **Most challenging AI interaction:** id="006" — getting the loop's graceful-exit handling correct across `exit`/`quit`/`:q`, Ctrl+C, Ctrl+D, and SIGINT during I/O.
- **Biggest lesson learned:** Treat every prompt like a contract: name the file, name the success criteria, name the error paths. Vague prompts produce code that demos well and breaks under real use.

---

**Note:** This log is a required component of your final project report. Be thorough and honest in your documentation to demonstrate your learning process and AI collaboration skills.
