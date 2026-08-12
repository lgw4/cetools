# Changelog

All notable changes to cetools are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Versioning is CalVer in `YYYY.0M.INC1` form: `2026.08.1` is the first
release cut in August 2026, `2026.08.2` the second. Because CalVer says
nothing about compatibility, breaking changes get their own **Breaking
changes** heading in the entry that ships them.

## 2026.08.1 (unreleased)

First release: the dice and 2D6 task-check engine, as a library and a CLI.

### Added

- **Seeded dice rolling.** `Roller` wraps a seeded generator; `throw`,
  `throw_dice`, and `parse_notation` handle `NdN`, `NdN+M`, and `NdN-M`
  notation, returning a frozen `ThrowResult` carrying the individual dice,
  the modifier, the total, and the seed.
- **`d66`.** The two-digit table die, read as tens and units rather than
  summed, for the SRD's 36-entry tables.
- **2D6 task resolution.** `check` resolves a task against a target number,
  applying difficulty, characteristic, and skill modifiers plus any number
  of ad-hoc situational DMs, and returns a `CheckResult` with every modifier
  itemised and named. An omitted characteristic contributes no modifier
  rather than a silent zero; skill level 0 means trained-but-unpracticed and
  is distinct from no training at all, which takes the unskilled DM.
- **SRD parameters as data.** Target number, difficulty DMs, characteristic
  DM bands, and the unskilled DM live in `src/cetools/data/tasks.toml` and
  are read at runtime by `load_task_parameters`. The engine hard-codes no
  table content, so house rules are a data edit.
- **`cetools roll` and `cetools check`.** Both accept `--seed`, print the
  seed they used (freshly generated if none was given), and accept `--json`
  for machine-readable output. `cetools --version` reports the version.
- **Rendering.** `as_text`, `as_dict`, and `as_json` render any result type
  for display or for machines, and are available to library consumers, not
  just the CLI.
- **Error hierarchy.** `CetoolsError` with `DiceError`, `RulesDataError`,
  and `TaskError` beneath it. The library raises; it never prints and never
  exits. The CLI is what turns an error into a stderr message and a non-zero
  exit code.
- **Reproducibility guarantee.** The same seed and the same package version
  produce the same result, verified by a dedicated guard suite alongside
  unit, integration, contract, property, and golden-output tests.
- **Dual licensing.** `LICENSE` (GPL-3.0) covers the code; `LICENSE-OGL.txt`
  (OGL 1.0a, with the SRD's Section 15 chain verbatim) covers
  `src/cetools/data/tasks.toml` as Open Game Content. Both ship in every
  sdist and wheel.
- **Project documentation.** `README.md` with installation and worked
  examples, and `CONTRIBUTING.md` covering the constitution, the spec-driven
  workflow, and the licensing rules.
