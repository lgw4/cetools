# Batch Character Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `cetools character generate` produce N characters in one run, either all of one career (`--career X -n N`) or each with a uniform-random career (`--random -n N`), while leaving single-character and draft behavior unchanged.

**Architecture:** Add one single-character engine function (`random_career_character`) mirroring the existing `draft_character`; add one formatter helper (`format_characters`) that joins blocks with a blank line; the CLI owns the count loop, mode dispatch, and mutual-exclusion validation. Each engine entry point stays single-character and composable.

**Tech Stack:** Python 3.14, Typer (CLI), pytest + coverage, Black, flake8, isort, managed with `uv`.

## Global Constraints

- Format with Black and lint with flake8 before finishing: `uv run black . && uv run flake8 src tests`.
- Full suite must pass with coverage ≥ 85%: `uv run pytest`.
- Conventional Commits for every commit message.
- Tests mirror package structure under `tests/`; reuse the roller fakes in `tests/conftest.py` (`ConstantRoller`, `SmartRoller`, `SequenceRoller`) — do not add new global roller classes.
- `DiceRoller.roll(sides, count=1)` returns the summed roll in `1..sides*count`; a single `roll(n)` returns `1..n` and is the idiom for picking from an n-element list (see `_draw_distinct`).
- Career selection must be reproducible under a seeded/fake roller: derive the career list with `sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)`.

---

### Task 1: Engine — `random_career_character`

**Files:**
- Modify: `src/cetools/engine/generator.py` (add function near `draft_character` at end of file)
- Test: `tests/test_generator.py`

**Interfaces:**
- Consumes: `CAREER_REGISTRY` (already imported in `generator.py`), `generate_career_character(career, roller=None, drafted=False)`, `RandomDiceRoller`, `DiceRoller`, `Character`, `GenerationFailure` (all already imported in `generator.py`).
- Produces: `random_career_character(roller: DiceRoller | None = None, drafted: bool = False) -> Character | GenerationFailure` — picks a career uniformly at random from the full registry and generates one character of it.

Reference facts (verified): with `sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)`, index `0` is `"Aerospace System Defense"` and index `8` is `"Drifter"` (the only career with no qualification). A `SequenceRoller([9], default=10)` picks index `(9-1) % 24 = 8` → Drifter and generates cleanly; `SequenceRoller([1], default=10)` picks index `0` → Aerospace System Defense.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_generator.py`. First, extend the existing import from `cetools.engine.generator` to include `random_career_character` (add it to the existing multi-name import block alphabetically, after `roll_until_qualified`). Then append these tests:

```python
def test_random_career_character_selects_career_by_first_roll() -> None:
    # SequenceRoller first value 9 -> pick index (9-1) % 24 = 8 -> Drifter
    # (Drifter has no qualification, so generation completes with default rolls)
    result = random_career_character(SequenceRoller([9], default=10))
    assert isinstance(result, Character)
    assert result.career == "Drifter"


def test_random_career_character_varies_with_first_roll() -> None:
    drifter = random_career_character(SequenceRoller([9], default=10))
    aerospace = random_career_character(SequenceRoller([1], default=10))
    assert aerospace.career == "Aerospace System Defense"
    assert drifter.career != aerospace.career


def test_random_career_character_passes_drafted_through() -> None:
    result = random_career_character(SequenceRoller([9], default=10), drafted=True)
    assert isinstance(result, Character)
    assert result.drafted is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_generator.py -k random_career_character -v --no-cov`
Expected: FAIL — `ImportError` / `cannot import name 'random_career_character'`.

- [ ] **Step 3: Add the implementation**

Append to the end of `src/cetools/engine/generator.py`:

```python
def random_career_character(
    roller: DiceRoller | None = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    if roller is None:
        roller = RandomDiceRoller()
    careers = sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)
    idx = (roller.roll(len(careers)) - 1) % len(careers)
    return generate_career_character(careers[idx], roller, drafted=drafted)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -k random_career_character -v --no-cov`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: add random_career_character engine helper"
```

---

### Task 2: Formatter — `format_characters`

**Files:**
- Modify: `src/cetools/formatter.py` (add function after `format_character`)
- Test: `tests/test_formatter.py`

**Interfaces:**
- Consumes: `format_character(character: Character) -> str` (already in this file), `Character` (already imported).
- Produces: `format_characters(characters: list[Character]) -> str` — joins each `format_character` block with a single blank line (`"\n\n"`). Empty list → `""`; single-element list → identical to `format_character`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_formatter.py`. Extend the top import to `from cetools.formatter import format_character, format_characters`, then append:

```python
def test_format_characters_empty_list_is_empty_string() -> None:
    assert format_characters([]) == ""


def test_format_characters_single_matches_format_character() -> None:
    character = _make_full_character()
    assert format_characters([character]) == format_character(character)


def test_format_characters_joins_blocks_with_blank_line() -> None:
    a = _make_full_character()
    b = _make_empty_character()
    expected = f"{format_character(a)}\n\n{format_character(b)}"
    assert format_characters([a, b]) == expected
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_formatter.py -k format_characters -v --no-cov`
Expected: FAIL — `ImportError` / `cannot import name 'format_characters'`.

- [ ] **Step 3: Add the implementation**

Append to `src/cetools/formatter.py`:

```python
def format_characters(characters: list[Character]) -> str:
    return "\n\n".join(format_character(character) for character in characters)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_formatter.py -k format_characters -v --no-cov`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/cetools/formatter.py tests/test_formatter.py
git commit -m "feat: add format_characters batch formatter"
```

---

### Task 3: CLI — `--count`/`-n` and `--random` on `generate`

**Files:**
- Modify: `src/cetools/cli/character.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `random_career_character` (Task 1), `format_characters` (Task 2), existing `draft_character`, `generate_career_character`, `CAREER_REGISTRY`, `Character`, `GenerationFailure`.
- Produces: updated `generate` command accepting `--random` (bool, default `False`) and `--count`/`-n` (int, default `1`, min `1`). `--career` + `--random` is rejected (exit 1). Output is always routed through `format_characters`.

The current `generate` resolves/validates `--career` (with fuzzy-match on unknown) then generates one character. This task keeps that validation, adds mode dispatch, and loops `count` times. Failure handling: generation in these modes is roll-until-qualified so `GenerationFailure` is practically unreachable; if one occurs, print its `reason` to stderr, skip it, keep going, and exit 1 at the end if any failed.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`. The existing `random_career_character` will need patching, so patch it at `cetools.cli.character.random_career_character`. Append:

```python
def test_count_generates_multiple_drafted_characters():
    with patch(
        "cetools.cli.character.draft_character", return_value=_make_character()
    ) as mock_draft:
        result = runner.invoke(app, ["character", "generate", "-n", "3"])
    assert result.exit_code == 0
    assert mock_draft.call_count == 3
    assert result.stdout.count("Navy (7 terms)") == 3


def test_count_with_career_generates_multiple_of_that_career():
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=_SCOUT_CHARACTER,
    ) as mock_gen:
        result = runner.invoke(
            app, ["character", "generate", "--career", "scout", "-n", "2"]
        )
    assert result.exit_code == 0
    assert mock_gen.call_count == 2
    assert result.stdout.count("Scout (1 terms)") == 2


def test_random_flag_uses_random_career_character():
    with patch(
        "cetools.cli.character.random_career_character",
        return_value=_make_character(),
    ) as mock_random:
        result = runner.invoke(app, ["character", "generate", "--random", "-n", "2"])
    assert result.exit_code == 0
    assert mock_random.call_count == 2


def test_default_generate_still_single_draft():
    with patch(
        "cetools.cli.character.draft_character", return_value=_make_character()
    ) as mock_draft:
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 0
    assert mock_draft.call_count == 1
    assert result.stdout.count("Navy (7 terms)") == 1


def test_career_and_random_are_mutually_exclusive():
    result = runner.invoke(
        app, ["character", "generate", "--career", "scout", "--random"]
    )
    assert result.exit_code == 1
    assert "mutually exclusive" in result.stderr


def test_count_below_one_is_rejected():
    result = runner.invoke(app, ["character", "generate", "-n", "0"])
    assert result.exit_code == 2  # Typer validation error


def test_batch_reports_failure_and_continues():
    failure = GenerationFailure(reason="boom")
    with patch(
        "cetools.cli.character.random_career_character",
        side_effect=[_make_character(), failure, _make_character()],
    ) as mock_random:
        result = runner.invoke(app, ["character", "generate", "--random", "-n", "3"])
    assert mock_random.call_count == 3
    assert result.exit_code == 1
    assert "boom" in result.stderr
    assert result.stdout.count("Navy (7 terms)") == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -k "count or random or mutually or default_generate or batch" -v --no-cov`
Expected: FAIL — new options not defined / `random_career_character` not importable from `cetools.cli.character` / assertions on call counts fail.

- [ ] **Step 3: Update the CLI**

Replace the entire contents of `src/cetools/cli/character.py` with:

```python
import difflib
from typing import Annotated

import typer

from cetools.engine.careers import CAREER_REGISTRY
from cetools.engine.generator import (
    draft_character,
    generate_career_character,
    random_career_character,
)
from cetools.engine.models import Character
from cetools.formatter import format_characters

app = typer.Typer()

_CANONICAL_CAREERS = ", ".join(
    c.name for c in sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)
)


@app.command()
def generate(
    career: Annotated[
        str | None,
        typer.Option("--career", help=f"Career to generate. Valid careers: {_CANONICAL_CAREERS}"),
    ] = None,
    random: Annotated[
        bool,
        typer.Option("--random", help="Draw each career uniformly at random from all careers."),
    ] = False,
    count: Annotated[
        int,
        typer.Option("--count", "-n", min=1, help="Number of characters to generate."),
    ] = 1,
) -> None:
    """Generate one or more characters."""
    if career is not None and random:
        typer.echo("Options --career and --random are mutually exclusive.", err=True)
        raise typer.Exit(1)

    resolved_career = None
    if career is not None:
        original = career
        normalized = career.strip().lower().replace("-", " ")
        if normalized not in CAREER_REGISTRY:
            matches = difflib.get_close_matches(
                normalized, CAREER_REGISTRY.keys(), n=1, cutoff=0.6
            )
            if matches:
                canonical = CAREER_REGISTRY[matches[0]].name
                typer.echo(
                    f"Unknown career '{original}'. Did you mean: {canonical}?",
                    err=True,
                )
            else:
                typer.echo(
                    f"Unknown career '{original}'. Valid careers: {_CANONICAL_CAREERS}",
                    err=True,
                )
            raise typer.Exit(1)
        resolved_career = CAREER_REGISTRY[normalized]

    characters: list[Character] = []
    failures = 0
    for _ in range(count):
        if resolved_career is not None:
            result = generate_career_character(resolved_career)
        elif random:
            result = random_career_character()
        else:
            result = draft_character()

        if isinstance(result, Character):
            characters.append(result)
        else:
            typer.echo(result.reason, err=True)
            failures += 1

    if characters:
        typer.echo(format_characters(characters))
    if failures:
        raise typer.Exit(1)
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -k "count or random or mutually or default_generate or batch" -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Run the full CLI test file to catch regressions**

Run: `uv run pytest tests/test_cli.py -v --no-cov`
Expected: PASS — including the pre-existing single-character and enlistment-failure tests.

- [ ] **Step 6: Commit**

```bash
git add src/cetools/cli/character.py tests/test_cli.py
git commit -m "feat: generate multiple characters with --count and --random"
```

---

### Task 4: Full verification and docs

**Files:**
- Possibly modify: `README.md` (only if it documents `character generate` usage)

- [ ] **Step 1: Format and lint**

Run: `uv run black . && uv run flake8 src tests`
Expected: Black reports files unchanged (or reformats cleanly); flake8 reports no errors.

- [ ] **Step 2: Run the full suite with coverage**

Run: `uv run pytest`
Expected: PASS with coverage ≥ 85%.

- [ ] **Step 3: Smoke-test the real CLI**

Run: `uv run cetools character generate --random -n 3`
Expected: three character blocks separated by a blank line, careers varying.

Run: `uv run cetools character generate --career scout -n 2`
Expected: two Scout characters.

Run: `uv run cetools character generate --career scout --random`
Expected: stderr "Options --career and --random are mutually exclusive." and exit code 1 (check with `echo $status` in fish).

- [ ] **Step 4: Update README if needed**

Check whether `README.md` documents `character generate`. If it lists options/usage, add `--count/-n` and `--random` with a one-line example each, matching the existing style. If the README does not cover command options, skip this step.

- [ ] **Step 5: Commit any doc changes**

```bash
git add README.md
git commit -m "docs: document --count and --random for character generate"
```

(Skip this commit if the README needed no changes.)
```

## Notes for the implementer

- Do not add batch/loop logic to the engine — the engine exposes single-character functions and the CLI owns iteration and formatting.
- The `--random` parameter name shadows nothing imported in `cli/character.py`; keep the explicit `"--random"` option string so Typer names the flag correctly.
- `GenerationFailure.exit_code` defaults to `1`; the batch path intentionally uses a plain `Exit(1)` after reporting failures rather than per-failure exit codes.
