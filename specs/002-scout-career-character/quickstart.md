# Quickstart Validation Guide: Scout Career & Career Selection Flag

**Feature**: 002-scout-career-character | **Date**: 2026-06-18

This guide documents runnable validation scenarios to confirm the feature works end-to-end. It does not contain implementation code or full test suites; those belong in `tasks.md` and `tests/`.

---

## Prerequisites

```bash
uv sync
```

Installs the project and all dev dependencies.

---

## Scenario 1: Generate a Scout character via `--career`

**Purpose**: Verifies SC-001 — a complete Scout character is always returned with Intelligence 6+.

```bash
uv run cetools character generate --career scout
```

**Expected output** (abbreviated; exact values vary by random rolls):

```
UPP: xxxxxxx

Scout (Scout, Rank 0) — N terms, age A

Characteristics:
  ...
  Intelligence: 6   ← must be 6 or higher
  ...

Skills:
  Piloting-1, ...   ← Piloting must be present at level 1 or higher

Mustering-Out Benefits:
  ...
```

**Checks**:
- Exit code is 0.
- `Intelligence` value in Characteristics is ≥ 6.
- `Piloting` is present in Skills at level ≥ 1 (rank-0 bonus).
- Career line reads `Scout (Scout, Rank 0)` with no "(Drafted)".

Run this several times; all invocations should succeed (re-roll guarantees qualification).

---

## Scenario 2: Default to draft (no `--career` flag)

**Purpose**: Verifies SC-002 — without `--career`, the character is draft-assigned and output includes "(Drafted)".

```bash
uv run cetools character generate
```

**Expected output** (abbreviated):

```
UPP: xxxxxxx

Navy (Drafted) (Starman, Rank 0) — N terms, age A
```

or

```
Scout (Drafted) (Scout, Rank 0) — N terms, age A
```

**Checks**:
- Exit code is 0.
- Career line contains "(Drafted)".
- Career is either `Navy` or `Scout`.

Run several times to observe both Navy and Scout outcomes from the draft table (statistically, 5/6 Navy, 1/6 Scout).

---

## Scenario 3: Navy by career flag

**Purpose**: Verifies SC-003 path for Navy and confirms existing Navy behavior is unchanged (FR-014).

```bash
uv run cetools character generate --career navy
```

**Expected output** (abbreviated):

```
UPP: xxxxxxx

Navy (Starman, Rank 0) — N terms, age A
```

**Checks**:
- Exit code is 0.
- Career line reads `Navy (...)` with no "(Drafted)".
- `Intelligence` value is ≥ 6.

---

## Scenario 4: Unrecognized career name

**Purpose**: Verifies SC-005 — unrecognized career exits with code 1 and a human-readable error.

```bash
uv run cetools character generate --career marine
echo "Exit code: $?"
```

**Expected output**:

```
Unknown career 'marine'. Valid careers: navy, scout
Exit code: 1
```

**Checks**:
- Error message goes to stderr (not stdout).
- Exit code is 1.
- Original unmodified input value appears in the error (`marine`).

---

## Scenario 5: Case-insensitive `--career` normalization

**Purpose**: Verifies FR-007 — mixed case and whitespace are accepted.

```bash
uv run cetools character generate --career Scout
uv run cetools character generate --career SCOUT
```

Both should behave identically to `--career scout` (exit 0, valid Scout character).

---

## Automated Test Verification

After implementation, the full suite must pass:

```bash
uv run black . && uv run flake8 src tests && uv run pytest
```

Key test targets:
- `tests/test_generator.py` — `roll_until_qualified`, `generate_career_character`, `draft_character`
- `tests/test_careers.py` — Scout data structure correctness
- `tests/test_cli.py` — `--career` flag, draft default, error messages, exit codes
- `tests/test_formatter.py` — `(Drafted)` rendering

For contract details (exact error messages, exit codes, output format), see [contracts/cli.md](contracts/cli.md).
For entity shapes and field definitions, see [data-model.md](data-model.md).
