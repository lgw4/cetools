# Contributing

## Setup

```bash
git clone <repo>
cd cetools
uv sync
uv run pre-commit install --hook-type pre-push
```

`uv sync` installs the package and all dev dependencies (`pytest`, `pytest-cov`,
`pytest-timeout`, `black`, `isort`, `flake8`, `pre-commit`) into `.venv`. The
`pre-commit install` step is one-time per clone: it installs the pre-push hooks
that run the quality gate below before every `git push`.

## Project layout

```
src/cetools/
├── cli/            # Typer CLI—thin I/O wrapper only, no game logic
│   ├── main.py     # Root app; registers sub-apps
│   ├── character.py
│   ├── world.py    # `cetools world` sub-app: generate, subsector
│   └── ship.py     # `cetools ship` sub-app: build, generate
├── engine/         # Pure generation engine—no CLI dependency
│   ├── careers/
│   │   ├── __init__.py   # The package's public surface; import from here
│   │   ├── base.py       # Career + RankEntry frozen dataclasses
│   │   ├── navy.py       # NAVY_CAREER instance (one module per career, 24 of them)
│   │   └── registry.py   # CAREERS, DRAFT_TABLE, resolve(), is_military(), UnknownCareer
│   ├── worlds/
│   │   ├── __init__.py   # The package's public surface; import from here
│   │   ├── tables.py     # SRD Chapter 12 tables as data: sizes, atmospheres, DMs, trade codes
│   │   ├── models.py     # World, System, Subsector, TravelZone, Density frozen dataclasses
│   │   ├── generator.py  # generate_world/system/subsector(rolls, ...)
│   │   ├── naming.py     # generate_world_name()
│   │   └── profile.py    # render_profile(), render_data_line()
│   ├── ships/
│   │   ├── __init__.py   # The package's public surface; import from here
│   │   ├── tables.py     # SRD ship-construction tables as data: hulls, drives, armor, turrets, bays, screens
│   │   ├── models.py     # ShipDesign, Ship, Crew, LineItem and the frozen component-fit records
│   │   ├── builder.py    # build_ship(design): the sole costing/validation authority
│   │   ├── generator.py  # generate_ship(rolls, ...): rolls a legal ShipDesign, then builds it
│   │   ├── names.py      # ShipName, SHIP_NAMES, generate_ship_name(rolls): curated name catalog
│   │   ├── design.py     # load_design/loads_design/dump_design: TOML round-trip
│   │   ├── prose.py      # number, word and list formatting primitives for the description
│   │   └── description.py # render_description(ship)
│   ├── notation.py     # spell/numbers: how a set of acceptable values is written
│   ├── rolls.py        # Rolls seam: RollName, RandomRolls, ScriptedRolls, RecordingRolls
│   ├── rules.py        # Rules policy: HOUSE (default) and SRD
│   ├── generator.py    # generate(assignment, rolls, rules): the coordinator
│   ├── background.py   # background_skills()
│   ├── ranks.py        # progress(): Commission and Advancement
│   ├── training.py     # roll_skill(), rolls_this_term(): Skills and Training
│   ├── aging.py        # apply_aging()
│   ├── benefits.py     # muster_out()
│   ├── mishaps.py      # resolve_survival_mishap()
│   ├── psionics.py     # roll_psionics()
│   ├── names.py        # generate_name()
│   ├── models.py       # Character, Benefit variants, Term, GenerationFailure,
│   │                   # characteristic_check(), parse/apply_stat_boost()
│   └── pseudohex.py    # Pseudo-hex encode/decode
└── formatter.py    # Plain-text character formatter

tests/              # Mirrors src/cetools/ structure
└── data/           # Test fixtures: ships/ design files, baseline/ regression captures
scripts/
└── check_docs.py   # The docs check; part of the quality gate below
```

The engine (`src/cetools/engine/`) must never import from `src/cetools/cli/`. The CLI is the only code allowed to depend on the engine.

Within the engine, `careers`, `worlds` and `ships` are imported as packages: each
`__init__.py` is the public surface, so a caller reaches for `CAREERS` or
`resolve()` from `cetools.engine.careers`, not from `registry.py`, and for
`build_ship` or `generate_ship` from `cetools.engine.ships`, not from
`builder.py` or `generator.py`.

## Quality gate

Run this before every commit:

```bash
uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

All five must pass, and the pre-push hooks run all five. `pytest` includes
coverage measurement; the suite fails if `src/cetools` coverage drops below 85%.

`scripts/check_docs.py` is the only thing that tests the docs, which is why it exists: docs drift faster than code and nothing else notices. It checks that every backticked symbol in the maintained prose resolves in the package, that the README's Python examples still run, that the module map above names every engine module, and that dashes are tight.

To run a single test file without coverage enforcement:

```bash
uv run pytest tests/test_foo.py --no-cov
```

## Engineering principles

**SRD fidelity.** The [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/index.html)
is the authority on game rules. Tables are transcribed as data, separate from the code
that reads them, and verified against the SRD text rather than against memory or another
implementation. Any deliberate departure from the SRD must be a named, selectable policy
rather than a silent default—house rules live behind `rules.py`'s `HOUSE` versus `SRD`
value, and every departure must be documented in user-facing prose where a referee will
see it. An undocumented divergence from the SRD is a defect.

**Test-first.** Strict red-green TDD: write a test that specifies the desired behavior,
run it and observe it fail for the expected reason, write the minimum implementation
that makes it pass, then run the suite green and refactor with the suite still green.
Skipping the observed-failure step is a violation even when the implementation is
obvious—a test that passes before the implementation exists is not evidence. Tests
mirror the source layout (`src/cetools/engine/foo.py` → `tests/test_foo.py`).

**Determinism.** Every random decision the rules make passes through the single `Rolls`
seam in `src/cetools/engine/rolls.py` and is named in `RollName`; direct use of the
`random` module outside that seam is prohibited in engine code. Given the same seed and
inputs, generation produces identical output—this is a correctness property rather than
a testing convenience, since it is what makes `--seed` meaningful. Tests script rolls
with `ScriptedRolls` rather than seeding `RandomRolls` and asserting on whatever emerges.

A scripted check answers with an outcome and reads neither the DM nor the target, so
scripting alone cannot tell whether a caller handed the seam the right ones—a career
surviving on the wrong characteristic against the wrong number reads exactly the same.
Where the *arguments* are the rule under test, wrap the adapter in `RecordingRolls` and
assert on the `Draw` records it keeps: `ScriptedRolls` says what the dice said,
`RecordingRolls` says what the engine asked.

**Simplicity.** YAGNI applies at every level: three similar lines are preferable to a
premature abstraction, and a concrete function is preferable to a configurable one.
Design for the requirement in hand, not a hypothetical successor.

**Versioning.** The package version in `pyproject.toml` and release tags use CalVer in
YYYY.0M.INC1 format (YYYY the year, 0M the zero-padded month, INC1 an increment
resetting to 1 each month)—e.g. `2026.07.1`, `2026.07.2`, `2026.08.1`. Version numbers
carry no compatibility semantics; breaking changes are communicated in the changelog and
commit history. PEP 440 normalization strips the month's leading zero, so `2026.07.1`
and `2026.7.1` are the same version and both appear correctly—`2026.07.1` in
`pyproject.toml`, `2026.7.1` in `uv.lock` and from Python's package metadata. This is
expected and must not be "corrected" by unpadding the authored form.

## Adding a new career

All 24 SRD careers are implemented, so this is mostly a recipe for house careers
and for correcting an existing one.

1. Create `src/cetools/engine/careers/<name>.py` with a `Career` instance built from the `Career` frozen dataclass in `base.py`. It is pure data: targets, the four skill tables, `ranks`, and the two benefit tables. No logic.
2. Register it in `src/cetools/engine/careers/registry.py` by adding it to `CAREERS` (and to `DRAFT_TABLE` if it is a draftable military service, which is also what makes it military). `CAREERS` sorts by name and the lookup key is `name.lower()`, so there is nothing else to keep in sync.
3. Add `tests/test_<name>_career.py` asserting data-structure integrity: the scalar targets, each skill table, the ranks, and the benefit tables, checked against the SRD. `tests/test_careers.py` covers the cross-career rules and needs no new case.
4. Add the career to the README's supported-careers list.

No changes to `generator.py` or the CLI are required or expected: `--career`
resolves against `CAREERS` through `resolve()`, and `--random` draws from it, so
a registered career is selectable the moment it exists.

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
feat: add Scout career
fix: correct Navy advancement target
docs: update README example output
test: add aging edge-case coverage
```

## Pull requests

- One logical change per PR.
- The quality gate must pass on the PR branch before review.
- PR title follows Conventional Commits (same format as commits above).
