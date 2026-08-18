# Changelog

All notable changes to cetools are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Versioning is CalVer in `YYYY.0M.INC1` form: `2026.08.1` is the first
release cut in August 2026, `2026.08.2` the second. Because CalVer says
nothing about compatibility, breaking changes get their own **Breaking
changes** heading in the entry that ships them.

PEP 440 normalizes the zero-padded month away, so the version installed
metadata reports — and therefore the version `cetools` prints in its
provenance block — drops it: `2026.08.1` here is `2026.8.1` there. The two
name the same release.

## 2026.08.1 (unreleased)

First release: the dice and 2D6 task-check engine, as a library and a CLI.

### Breaking changes

- **`load_task_parameters` is removed.** Read `load_rules().task_parameters`
  instead. `check`'s `parameters=` keyword is removed too, replaced by
  `rules=`, which takes a `RulesData` rather than a bare `TaskParameters`.
  Package version `2026.08.1` is unreleased, so no published consumer is
  affected.

### Added

- **Validated rules data loading.** `load_rules` and `validate_rules`
  discover every `.toml` file under `cetools/data/`, compose it with an
  optional override, and validate the whole set on every load: a data set
  loads only when all of it is well-formed, or refuses, naming every problem
  it finds in one run rather than the first. A file that is present but
  cannot be read is reported like any other problem, naming the file, and the
  remaining files are still checked rather than masked by it. A file rejected
  on its header — an unsupported `schema-version`, an unrecognized kind — is
  reported once and its contents left uninterpreted, and it is never then also
  reported absent, because it is sitting in the data set. A `schema-version`
  is typed before it is compared, so `true` and `1.0` are refused as the
  wrong type rather than passing the gate on Python's `True == 1`. A problem
  about a value's type names both types the way the data files spell them —
  `found a string; expected an integer` — and a problem concerning two files
  names both in what it found while keeping its file key singular, so
  grepping the report by filename finds every problem about that file.
  `RulesData` carries the loaded set; `ValidationReport` carries a report of
  what is wrong, if anything, and the two agree on every input.
- **The compact table notation.** `parse_entry` reads a career table cell in
  any of its four forms — a characteristic check, a characteristic
  adjustment, a skill grant, or a bare name — governed by the `EntryContext`
  the field it came from admits. It returns a `NotationProblem` rather than
  raising for a malformed entry or a form its context does not admit, so a
  caller can collect every problem in one pass, and that problem reports the
  entry exactly as written along with the forms admissible in the position it
  sits in, which is one form for a table's gate and two for a mustering-out
  benefits entry. A parenthesized specialty belongs to a skill or a benefit
  item, so one written on a characteristic — `INT (Foo) 4+` — is reported
  rather than quietly discarded; a specialty may end in a digit, so
  `Blade (Mark 2)` reads as the same skill and specialty its grant form
  `Blade (Mark 2) 1` does. The space before a specialty group is part of the
  grammar rather than decoration, so `Blade(Cutlass)` is reported as
  malformed rather than read as `Blade (Cutlass)`, and a benefit item
  resolves under the name as written, so `Weapon  (Blade)` is not silently
  collapsed into the registry's `Weapon (Blade)`.
- **The reference career, and the registries that give it meaning.** Three
  shipped registries (`CharacteristicRegistry`, `SkillRegistry`,
  `BenefitRegistry`) resolve the names a career file's entries use, the skill
  registry reporting which of the four `SkillResolution` outcomes a reference
  produces. A name no registry contains is reported with the registry it was
  checked against, so an author knows which file to correct, and a skill
  registry entry that spells a specialty into its own name — `"Gun Combat
  (Slug Rifle)"` — is refused rather than admitted as an entry no career
  could ever reference.
  `CareerDefinition` and its parts (`Throw`, `SkillTable`,
  `RankLadder`, `Rank`, `MusteringOut`) are the schema a career file
  validates against.
  The Navy ships as the reference career, exercising every element of that
  schema.
- **House rules without forking code.** `load_rules(override)` and
  `validate_rules(override)` accept a directory or a single file, composed
  over the packaged data set by basename: a file that matches a packaged
  name replaces it, one that does not is an addition, and everything the
  override does not touch still comes from the packaged data. A location that
  does not exist, or that is neither a file nor a directory, is refused as a
  usage error naming it, never quietly composed as the packaged set, and a
  directory within it that cannot be listed is reported the way an unreadable
  file is rather than passed over. Symlinked directories are followed, so a
  rule set assembled out of links composes. Files and directories whose names
  begin with a dot are passed over entirely when they are *found* under an
  override location, so pointing the tool at a git checkout reports nothing
  from `.git/` — and a `.toml` beneath such a directory does not quietly take
  effect either. A dot-prefixed path named on the command line is not passed
  over, because the author wrote it: `cetools validate ./.navy.toml` composes
  that file, rather than reporting success having done nothing. A file with
  the wrong extension is reported as ignored under its path within the
  override, so two files sharing a basename are both named. A FIFO or a
  symlink to a device node found within an override is reported rather than
  read, since either would otherwise hang the run forever with no output and
  no exit status. An empty override location is refused as a usage error too,
  rather than silently composing the current working directory, which is
  what the empty string names as a path.
- **Provenance.** Every `CheckResult` and `ValidationReport` carries a
  `Provenance`: the installed package version, and, for an overridden load,
  each file's disposition and a reproducible SHA-256 fingerprint over its
  raw bytes.
- **`cetools validate`.** Reports every problem in the packaged data set, or
  an override composed over it, with exit codes 0 (valid), 1 (invalid), and
  2 (usage error), in both text and `--json` output.
- **`--rules-data PATH` on `cetools check`.** Composes an override location
  over the packaged data set exactly as a library load does; the rendered
  and JSON output both gain a `Rules:` / `provenance` block reporting what
  produced the result.
- **Seeded dice rolling.** `Roller` wraps a seeded generator; `throw`,
  `throw_dice`, and `parse_notation` handle `NdN`, `NdN+M`, and `NdN-M`
  notation, returning a frozen `ThrowResult` carrying the individual dice,
  the modifier, the total, and the seed.
- **`d66`.** The two-digit table die, read as tens and units rather than
  summed, for the SRD's 36-entry tables.
- **2D6 task resolution.** `check` resolves a task against a target number,
  applying difficulty, characteristic, and skill modifiers plus any number
  of ad-hoc situational DMs, and returns a `CheckResult` with every modifier
  itemized and named. An omitted characteristic contributes no modifier
  rather than a silent zero; skill level 0 means trained-but-unpracticed and
  is distinct from no training at all, which takes the unskilled DM.
- **SRD parameters as data.** Target number, difficulty DMs, characteristic
  DM bands, and the unskilled DM live in `src/cetools/data/tasks.toml` and
  are read at runtime through `load_rules().task_parameters`. The engine
  hard-codes no table content, so house rules are a data edit.
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
- **Dual licensing.** `LICENSE` (GPL-3.0) covers the code, declared in the
  package metadata as the SPDX expression `GPL-3.0-only` so installers and
  indexes can read it; `LICENSE-OGL.txt` (OGL 1.0a, with the SRD's Section 15
  chain verbatim) covers every `.toml` file under `src/cetools/data/` — which
  ships as `cetools/data/` in an installed package, and the notice names both
  paths — as Open Game Content. Both ship in every sdist and wheel, and the
  guard that checks the notice's coverage derives what must be covered from
  the files a distribution actually carries, keyed on the designation rather
  than on a directory prefix and an extension. The sdist's `include` patterns
  for `README.md` and `CHANGELOG.md` are anchored to the repository root:
  unanchored, they matched at any depth and picked up a vendored Spec Kit
  file the sdist was never meant to ship.
- **Project documentation.** `README.md` with installation and worked
  examples, and `CONTRIBUTING.md` covering the constitution, the spec-driven
  workflow, and the licensing rules.
