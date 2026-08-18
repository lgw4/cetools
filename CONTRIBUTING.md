# Contributing to cetools

Thanks for your interest in cetools. This document covers how the project
is built, what a change is expected to look like, and the licensing rules
that constrain what may be added.

## The constitution comes first

`.specify/memory/constitution.md` is the governing document for this
repository. It supersedes this file and every other practice here; where
the two disagree, the constitution wins and this file is the thing that
needs fixing. Read it before your first change. Its six core principles,
in short:

1. **Library-first.** Every capability lives in the importable `cetools`
   library. The CLI is a thin consumer with no game logic of its own.
2. **CLI text I/O protocol.** Every library capability is reachable from
   the CLI. Results go to stdout, errors to stderr, every command offers
   both human-readable and `--json` output, and exit codes are meaningful.
3. **Test-first (non-negotiable).** Tests are written first, confirmed to
   fail, and only then is the implementation written.
4. **Seed-reproducible generation.** Every generator takes a seed, draws
   randomness from nothing but that seeded generator, and gives the same
   output for the same seed and package version.
5. **Data-driven rules content.** SRD rules content lives in data files
   under `src/cetools/data/`; engine code interprets the data and hard-codes
   no table content.
6. **Simplicity.** YAGNI governs. Speculative abstraction is rejected in
   review, the standard library is preferred, and every third-party runtime
   dependency must be justified by a concrete need.

Amendments go through `/speckit-constitution`, with a version bump, the
amendment date, and a rationale.

## Getting set up

Python 3.13 or newer, and [uv](https://docs.astral.sh/uv/):

```sh
uv sync
uv run pytest
```

That installs the package in editable form along with the dev group
(pytest, hypothesis, black, isort, flake8).

## How work is planned

cetools is developed with [Spec Kit](https://github.com/github/spec-kit).
Features are specified before they are written, and the artifacts live in
`specs/<NNN>-<slug>/` alongside the code. The usual arc for a non-trivial
change is:

1. `/speckit-specify` writes `spec.md` on a fresh `NNN-slug` branch.
2. `/speckit-clarify` resolves the underspecified parts.
3. `/speckit-plan` produces `plan.md`, `data-model.md`, `research.md`, and
   `contracts/`.
4. `/speckit-tasks` generates a dependency-ordered `tasks.md`.
5. `/speckit-analyze` checks the three for consistency.
6. `/speckit-implement` works the task list.

Small fixes (a typo, a one-line bug) do not need the full arc. Anything
that adds a capability, changes output, or touches the rules data does.

## Writing the change

**Tests first.** Principle III is marked non-negotiable and is enforced in
review: write the test, run it, watch it fail for the right reason, then
implement. The suite is organized by kind, and new tests belong in the
matching directory:

| Directory            | Purpose                                            |
| -------------------- | -------------------------------------------------- |
| `tests/unit/`        | One module's behavior in isolation                 |
| `tests/integration/` | CLI invocations end to end, and golden-file output |
| `tests/contract/`    | The stability of the `--json` shape                |
| `tests/property/`    | Hypothesis invariants over generated input         |
| `tests/guards/`      | The seed-reproducibility contract                  |
| `tests/golden/`      | Expected CLI text output, byte for byte            |

If your change alters human-readable CLI output, the golden files in
`tests/golden/` change with it in the same commit, and the diff should show
the new output plainly enough to be reviewed on sight.

**Anything new is reachable from both sides.** A new library function needs
a CLI path to it (Principle II), and a new CLI flag needs to be a thin call
into the library (Principle I). Both `as_text` and `as_dict`/`as_json` in
`src/cetools/render.py` need to know about any new result type.

**Randomness comes from the `Roller`.** Never call `random` directly, never
read the clock, never let a result depend on anything the seed does not
determine. `cetools.seeds.resolve_seed` turns a user-supplied string or
integer, or `None`, into the integer seed a `Roller` uses, and every command
prints the seed it used so any result can be regenerated.

**Rules content goes in the data files.** New difficulty bands, tables, or
task parameters are edits to `src/cetools/data/*.toml`, not new branches in
the engine. If the engine cannot express the rule from data, say so in the
spec and change the data format deliberately.

**Public API.** Anything exported from `cetools/__init__.py`'s `__all__`
carries a docstring; that is a requirement of Principle I, and
`tests/unit/` will not let it slide.

## Style and tooling

Formatting and linting are configured but, per Principle III, are not
constitutional gates. Run them anyway:

```sh
uv run black .
uv run isort .
uv run flake8
```

Line length is 99 for both black and flake8; isort uses the black profile.
CI (`.github/workflows/ci.yaml`) runs `uv run pytest` on Linux, macOS, and
Windows against Python 3.13 and 3.14. All six jobs must pass.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
with a scope naming the area touched:

```text
feat(dice): add d66 two-digit table die
docs(cetools): finish Phase 7 polish with docstrings and README usage
```

## Licensing, which is not optional

This repository carries two licenses, and mixing them up is the one mistake
that is genuinely hard to undo. Before adding a file, know which side of the
line it sits on.

- **Code, tests, packaging, and docs are GPL-3.0** (`LICENSE`). By
  contributing them you agree to license them that way.
- **Everything under `src/cetools/data/` is Open Game Content under OGL
  1.0a** (`LICENSE-OGL.txt`). It cannot be sublicensed under the GPL. Any new
  file containing content derived from the Cepheus Engine SRD is also OGC,
  must carry the OGC designation in a header comment the way `tasks.toml`
  does, and must live under `src/cetools/data/`, which is the directory the
  README's licensing section and the Section 15 game-data notice both
  designate. Putting one anywhere else means widening that notice in the same
  change; the guard below will tell you so.
- **Section 15 is verbatim.** Every distribution bundles the full OGL 1.0a
  text and reproduces the SRD's complete Section 15 copyright-notice chain
  exactly as received, extended with this project's own game-data copyright
  line. Do not reformat, abridge, or reword it.
- **Product Identity stays out.** The strings "Cepheus Engine" and
  "Samardan Press" must not appear in the package name or inside any shipped
  Open Game Content data file.
- **Compatibility claims carry attribution.** The README currently makes no
  compatibility claim and therefore owes no trademark attribution. If a
  change adds one, anywhere (README, PyPI description, CLI help), it adds
  the Compatibility-Statement License attribution ("Cepheus Engine and
  Samardan Press are the trademarks of Jason 'Flynn' Kemp") and a statement
  of non-affiliation in the same change.

`tests/unit/test_licensing.py` checks the mechanical parts of this: that
both license files exist and are non-empty, that `LICENSE-OGL.txt` still has
its Section 15 chain complete and in order, that `pyproject.toml` lists both
under `license-files` and declares the code's licence as the SPDX expression
`GPL-3.0-only`, that the README carries the OGC/GPL designation, that no
documented surface makes a compatibility claim without its attribution, and
that the chain's game-data notice covers every file carrying the OGC
designation — a check that reads the covered paths out of the notice itself,
so narrowing the notice fails rather than passing unnoticed.
`tests/guards/test_packaging.py` runs the same coverage check against the
built wheel and sdist, which is what SC-014 binds.

## Changelog and releases

Every user-visible change adds an entry to `CHANGELOG.md` under the
unreleased version, in the same commit as the change itself.

Versioning is CalVer, `YYYY.0M.INC1`: `2026.08.1` is the first release cut
in August 2026, `2026.08.2` the second. Because CalVer signals nothing about
compatibility, breaking changes are called out prominently in the changelog
entry, under their own heading. Releases are published to PyPI.

## Review

Pull requests and reviews verify compliance with the constitution's
principles. Complexity beyond the simplest adequate solution has to be
justified against Principle VI, in writing, in the PR description. A change
that is right but unexplained is likelier to be sent back than one that is
arguable and reasoned.
