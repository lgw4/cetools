# Batch character generation

## Goal

Let `cetools character generate` produce more than one character in a single
invocation, in two new modes:

1. **N of a given career** — generate a requested number of characters, all of
   the same career.
2. **N random careers** — generate a requested number of characters, each with a
   career drawn uniformly at random from all implemented careers.

Single-character generation and the existing draft default must continue to work
unchanged.

## CLI behavior

The feature is exposed by extending the existing `character generate` command
with a single new option and one new flag. No new subcommand is introduced.

- `--count` / `-n` (integer, default `1`, minimum `1`, enforced by Typer):
  number of characters to generate.
- `--random` (boolean flag, default off): draw each character's career uniformly
  at random from all implemented careers.

Mode is determined by the combination of `--career` and `--random`:

| Invocation | Result |
|---|---|
| `generate` | 1 drafted character (unchanged) |
| `generate -n 5` | 5 drafted characters |
| `generate --career agent -n 5` | 5 Agent characters |
| `generate --random -n 5` | 5 characters, each a uniform-random career from all 24 |
| `generate --career X --random` | error, exit code 1 (mutually exclusive) |

Notes:

- `--career X` continues to accept the existing fuzzy-match / unknown-career
  handling. When combined with `-n`, all N characters use that career.
- Omitting both `--career` and `--random` preserves today's behavior: a 1D6 roll
  on the six-career military draft table, repeated `count` times.
- `--random` draws from **all** implemented careers (the full
  `CAREER_REGISTRY`), not the six-career draft table.
- `--career` and `--random` are mutually exclusive. Passing both prints a clear
  error to stderr and exits with code 1.

## Distribution semantics for `--random`

Each of the N characters independently draws a career uniformly at random from
the full set of implemented careers. Exact per-career counts will vary between
runs (e.g. `-n 24 --random` will not necessarily yield one of each). "Evenly
distributed" here means equal probability per pick, not balanced final counts.

## Engine changes — `engine/generator.py`

Add one single-character function that mirrors the existing `draft_character`:

```python
def random_career_character(
    roller: DiceRoller | None = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    ...
```

Behavior:

- Build a deterministic, name-sorted list of careers from `CAREER_REGISTRY`.
- Pick one uniformly using `roller.roll(len(careers))` (the roller already
  supports arbitrary-sided rolls returning `1..n`, as used by `_draw_distinct`).
- Delegate to `generate_career_character(career, roller, drafted=drafted)`.

Sorting by name makes the selection reproducible under a seeded roller. No batch
loop is added to the engine — each engine entry point stays single-character and
composable, and the CLI owns iteration.

## Formatter changes — `formatter.py`

Add:

```python
def format_characters(characters: list[Character]) -> str:
    ...
```

It joins each `format_character(...)` block with a single blank-line separator
(no decorative rules, no numbered headers). Keeping the multi-character layout in
the formatter (rather than inline in the CLI) puts the presentation decision in
one testable place. An empty list yields an empty string; a single-element list
matches `format_character` output.

## CLI orchestration — `cli/character.py`

`generate` gains the `--count` and `--random` parameters and:

1. Rejects `--career` together with `--random` (stderr message, exit 1).
2. Resolves/validates `--career` as today when provided.
3. Loops `count` times, dispatching each iteration to the appropriate
   single-character engine function:
   - `--career X` → `generate_career_character(career)`
   - `--random` → `random_career_character()`
   - neither → `draft_character()`
4. Collects the results and prints them via `format_characters`.

### Failure handling

Career, random, and draft generation all roll-until-qualified and bypass
enlistment checks, so a `GenerationFailure` is practically unreachable in these
modes. If one does occur, the batch does not abort mid-run: its `reason` is
printed to stderr, that character is skipped, the remaining characters are still
generated and printed, and the command exits with a non-zero code at the end if
any character failed. (This is more batch-friendly than aborting on first
failure.)

## Testing

- `tests/test_generator.py`
  - `random_career_character` returns the expected career under a seeded/fixed
    roller.
  - Over many rolls it produces a spread across multiple distinct careers.
- `tests/test_formatter.py`
  - `format_characters` output for 0, 1, and N characters (separator correctness).
- `tests/test_cli.py`
  - `-n N` with `--career X` prints N blocks, all that career.
  - `--random -n N` prints N blocks.
  - `generate` and `generate -n 1` unchanged (1 block, draft).
  - `--career X --random` errors with exit code 1.

All new code has corresponding tests. The full suite (`uv run pytest`, with
coverage ≥ 85%), Black, and flake8 must pass before completion.

## Out of scope

- Balanced/round-robin distribution (exact per-career counts).
- Output formats other than the current text block (e.g. JSON, CSV).
- A separate `batch` subcommand.
- Parallelism or performance tuning for large N.
