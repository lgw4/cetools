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
│   └── world.py    # `cetools world` sub-app: generate, subsector
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
│   ├── rolls.py        # Rolls seam: RollName, RandomRolls, ScriptedRolls
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
scripts/
└── check_docs.py   # The docs check; part of the quality gate below
docs/adr/           # Architecture decision records
docs/superpowers/   # Historical plans and specs; a record, not documentation
specs/              # Spec Kit feature directories, one per feature, numbered
```

The engine (`src/cetools/engine/`) must never import from `src/cetools/cli/`. The CLI is the only code allowed to depend on the engine.

Within the engine, `careers` is imported as a package: its `__init__.py` is the
public surface, so a caller reaches for `CAREERS` or `resolve()` from
`cetools.engine.careers`, not from `registry.py`.

`CONTEXT.md` is the domain vocabulary: what a career, a term, a check, a mishap
and the `Rolls` seam mean here. Read it before naming anything new, and add an
entry when a new concept earns a name.

## Quality gate

Run this before every commit:

```bash
uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

All five must pass, and the pre-push hooks run all five. `pytest` includes
coverage measurement; the suite fails if `src/cetools` coverage drops below 85%.

`scripts/check_docs.py` is the only thing that tests the docs, which is why it exists: docs drift faster than code and nothing else notices. It checks that every backticked symbol in the maintained prose resolves in the package, that the README's Python examples still run, that the module map above names every engine module, and that dashes are tight. The historical plans and specs under `docs/superpowers/` are records of past decisions, not descriptions of the code, so they are not checked.

To run a single test file without coverage enforcement:

```bash
uv run pytest tests/test_foo.py --no-cov
```

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
