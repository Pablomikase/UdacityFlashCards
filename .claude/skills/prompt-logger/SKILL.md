---
name: prompt-logger
description: Capture every user prompt issued in the FlashcardQuizzer project into docs/prompts_log.xml as a refined English XML entry. Invoke after answering each substantive user prompt. Use a simple flat XML schema (role, task, context with nested tags) and let the user dictate which sections each entry includes.
---

# Prompt Logger

Keeps a versioned record of every prompt the student writes during the
AI-Assisted Development course. Entries live in `docs/prompts_log.xml` and are
refined into clear, technical English.

## When to invoke

**Invoke** after fulfilling each substantive user prompt in this project.

**Skip** when:
- The user explicitly opts out ("don't log this" / "no registres esto").
- The message is trivially conversational ("ok", "thanks", "yes", "no").
- The user is replying to a clarifying question this skill just asked — fold
  the answer into the in-progress entry instead of opening a new one.
- The message is a direct instruction to the logger itself ("delete entry 3",
  "fix the role in entry 7"). Carry it out without creating a new entry.

If unsure, log.

## Workflow

1. **Identify the prompt** that needs logging — the user's most recent
   substantive prompt in this session.
2. **Ask which sections to include** if the user hasn't already told you.
   Default sections are `role`, `task`, `context`. The user may add or omit
   any. Use `AskUserQuestion` only if it's genuinely unclear — otherwise
   propose a sensible set and let them override.
3. **Refine into English.** Imperative, technical, no filler. Preserve
   specifics (file paths, identifiers, libraries, versions, numbers).
4. **Append the entry** to `docs/prompts_log.xml`:
   - Compute the next sequential `id` (zero-padded to 3 digits).
   - Use today's date in `YYYY-MM-DD` format (from `currentDate` system
     context).
   - Insert the new `<prompt>` element immediately before the closing
     `</prompts_log>` tag, preserving two-space indentation.
5. **Confirm in one line.** `Logged prompt #NNN to docs/prompts_log.xml`.

## XML schema

Flat, prose-friendly, and shallow. Each entry is a `<prompt>` with `id` and
`date` attributes. Inside, group related ideas under a tag and write their
content as free-form prose or `-` bullet lists. Do **not** atomize every item
into its own child tag.

Common top-level tags (use only the ones that apply):

- `<role>` — persona / expertise the AI should adopt. One line of prose.
- `<task>` — the core instruction. One or two sentences of prose.
- `<context>` — surrounding information. Sub-tags are open vocabulary in
  snake_case; pick descriptive names that fit the prompt. Examples that have
  appeared:
  - General: `<application_type>`, `<tech_stack>`, `<user_workflow>`,
    `<runtime>`, `<starting_point>`, `<data_file>`
  - Testing prompts: `<class_under_test>`, `<test_categories>` (bullet list
    of categories such as happy path, error conditions, edge cases,
    integration points, performance)
  - Architecture prompts: `<current_architecture>`, `<integration_points>`,
    `<data_model>`
- `<requirements>` — what must be true of the result. May group sub-tags such
  as `<functional_requirements>`, `<extensibility_requirements>`,
  `<non_functional_requirements>`. Content is a `-` bullet list, **not**
  nested item tags.
- `<constraints>` — what limits the solution. May group sub-tags such as
  `<architecture_principles>`, `<complexity_limits>`, `<dependencies>`,
  `<style>`, `<security>`. Single-line prose or short bullet list.
- `<output_format>` — what the response must look like. Prose.
- `<success_criteria>` — `-` bullet list of acceptance checks.
- `<example>` (singular) — a concrete code snippet or pattern the AI should
  follow. Use one tag per example; do not wrap in `<examples>`/`<input>`/
  `<output>` ceremony unless the user explicitly asks for it. Place fenced
  code or short prose directly inside.
- `<thinking>` — chain-of-thought scratchpad the AI should fill in before
  answering. Pre-seed it with a `-` bullet list of the considerations the
  user wants the AI to weigh, optionally followed by a prose summary of what
  the AI needs to figure out. Use this when the prompt benefits from
  explicit deliberation (architecture choices, trade-off analysis, security
  reviews).

Don't invent sections the user didn't ask for. Don't pad with empty tags. If a
section would only hold one short fact, fold it into prose under a sibling tag
instead. The vocabulary above is illustrative — for any prompt, prefer
descriptive snake_case sub-tags over generic ones.

### Reference shape

```xml
<prompt id="NNN" date="YYYY-MM-DD">
  <role>Senior Python developer following SOLID principles</role>
  <task>
    Design architecture for a CLI expense tracker application
  </task>
  <context>
    <application_type>Command-line personal finance tool</application_type>
    <tech_stack>Python 3.8+, CSV file storage</tech_stack>
    <user_workflow>Load transactions → Select report mode → View summary</user_workflow>
  </context>
  <requirements>
    <functional_requirements>
- Support multiple report modes: summary by category, monthly totals, etc.
- Load transaction data from CSV files (date, description, category, amount)
- Display formatted reports in the terminal
- Track totals and provide accurate summaries
    </functional_requirements>
    <extensibility_requirements>
- Easy to add new report modes without modifying existing code
- Support for different data formats (e.g., JSON) in the future
- Configurable report formatting and display
    </extensibility_requirements>
  </requirements>
  <constraints>
    <architecture_principles>Follow SOLID principles explicitly</architecture_principles>
    <complexity_limits>Keep each module under 200 lines, single responsibility</complexity_limits>
    <dependencies>Standard library only, no external frameworks</dependencies>
  </constraints>
</prompt>
```

## Style rules

- English, imperative, technical. Strip "please", "can you", "I want".
- Preserve identifiers, paths, versions verbatim.
- Bullet lists use `-` inside the tag content. Do **not** wrap each item in a
  `<criterion>` / `<command>` / `<item>` tag.
- Keep nesting shallow — at most two levels deep inside a `<prompt>`.
- Wrap any text containing `<`, `>`, or `&` in `<![CDATA[...]]>`.
- Indent with two spaces for tags. Bullet lines inside a tag start at column 0
  of their own line for readability.
- Never include the original Spanish prompt in the file — only the refined
  English XML.

## Editing past entries

Edit surgically — never rewrite the whole file. When the user asks to amend or
delete an entry, locate it by `id` and modify only that block.
