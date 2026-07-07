# Design: Refresh README to match current cetools state

**Date:** 2026-07-06
**Status:** Approved

## Problem

`README.md` has drifted out of date. It documents an old verbose, multi-section
character output (UPP / Characteristics / Skills / Mustering-Out Benefits /
Retirement Pension) that no longer exists, lists only three careers, and shows a
library API whose return type has changed. Headline features shipped in specs
006–008 are undocumented.

## Ground truth (current code)

- **Output format** (spec 006, Universal Character Format): a compact,
  tab-delimited block of up to 5 lines with a generated name + rank title. The
  old per-characteristic list, cash/material split, and pension line are gone.
- **Careers**: four — Aerospace System Defense, Marine (new), Navy, Scout. A
  no-`--career` run drafts one via a Navy-skewed 1D6 table.
- **Mishaps replace death** (spec 007): a failed survival roll resolves on the
  Survival Mishaps table (injury, honorable, honorable+debt, dishonorable,
  dishonorable+imprisoned, medical) and always yields a usable character. Shown
  as a `Mishap:` line with optional injury/crisis/`Debt CrN` detail.
- **Benefit display** (spec 008): repeated material benefits collapse to `Name x N`.
- **CLI**: unknown `--career` does fuzzy "Did you mean…?" matching (difflib).
- **Library API**: `generate_career_character` and `draft_character` return
  `Character | GenerationFailure`; `Character` gained `name`, `rank_title`,
  `mishap`, `debt`.

## Goal

A README that accurately reflects the shipped tool, emphasizing the compact
output format: all four careers, mishaps, fuzzy career matching, and the current
library API, with a small curated set of real example outputs including one
showing a Mishap line.

## Decisions

- **Scope**: full refresh, not output-only.
- **Examples**: curated set (~3) with annotations, deliberately including a
  Mishap example, rather than one block per career.

## Changes (README.md, single deliverable)

1. Intro/careers line: list all four careers; note the random draft when
   `--career` is omitted.
2. CLI usage: add `marine`; keep the draft example; note fuzzy suggestion + exit 1
   on unknown `--career`.
3. Example output: replace all verbose blocks with a short format explanation
   plus three real, illustrative blocks — a clean run, a drafted run with
   collapsed `x N` benefits, and a mishap run (injury + crisis + debt).
4. Exit-code/pseudo-hex notes: keep pseudo-hex; drop the "character died" clause;
   describe exit 1 on unknown career or draft-path generation failure.
5. Library section: return type `Character | GenerationFailure`; list all four
   registry keys; keep the `DiceRoller` injection example; note new `Character`
   fields.

## Out of scope

No code changes. The `(N terms)` grammatical quirk (`1 terms`, `0 terms`) is
current output and is shown as-is. No changes to AGENTS.md / CONTRIBUTING.md.

## Verification

- Run the CLI for each career, a bare draft run, and a bad career name; confirm
  output matches the README line-for-line and the fuzzy message/exit code match.
- Run `uv run pytest` to confirm the repo is green (docs-only, no test impact).
