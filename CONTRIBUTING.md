# Contributing

## Setup

```bash
git clone <repo>
cd cetools
uv sync
```

`uv sync` installs the package and all dev dependencies (`pytest`, `pytest-cov`, `black`, `flake8`) into `.venv`.

## Project layout

```
src/cetools/
├── cli/            # Typer CLI — thin I/O wrapper only, no game logic
│   ├── main.py     # Root app; registers sub-apps
│   └── character.py
├── engine/         # Pure generation engine — no CLI dependency
│   ├── careers/
│   │   ├── base.py     # Career + RankEntry frozen dataclasses
│   │   └── navy.py     # NAVY_CAREER instance
│   ├── dice.py         # DiceRoller protocol + RandomDiceRoller
│   ├── generator.py    # generate_character() — the core state machine
│   ├── models.py       # Character, Skill, Benefit, Term, GenerationFailure
│   └── pseudohex.py    # Pseudo-hex encode/decode
└── formatter.py    # Plain-text character formatter

tests/              # Mirrors src/cetools/ structure
```

The engine (`src/cetools/engine/`) must never import from `src/cetools/cli/`. The CLI is the only code allowed to depend on the engine.

## Quality gate

Run this before every commit:

```bash
uv run black . && uv run flake8 src tests && uv run pytest
```

All three must pass. `pytest` includes coverage measurement; the suite fails if `src/cetools` coverage drops below 85%.

To run a single test file without coverage enforcement:

```bash
uv run pytest tests/test_foo.py --no-cov
```

## Adding a new career

1. Create `src/cetools/engine/careers/<name>.py` with a `Career` instance built from the `Career` frozen dataclass in `base.py`.
2. Add a corresponding test in `tests/test_careers.py` asserting data-structure integrity (table lengths, stat names, target values).
3. Wire a new CLI command in `src/cetools/cli/` if you want it exposed at the command line.

No changes to `generator.py` are required or expected.

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
