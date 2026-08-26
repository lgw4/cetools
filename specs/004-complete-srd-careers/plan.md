# Implementation Plan: Complete SRD Careers

**Branch**: `004-complete-srd-careers` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-complete-srd-careers/spec.md`

## Summary

Bring the package's career content to all twenty-four careers the source publishes,
reconciled field by field against one source of truth, and rebuild the skill and benefit
vocabularies to exactly what that source uses. Transcribing literally requires four data-shape
changes the current schema cannot express (an untitled rank, a short mustering-out table, a
rolled ship-share quantity, a cascade specialty that is itself a cascade), one dead field
removed (a characteristic on the re-enlistment throw), and one new invariant moved out of
documentation into `cetools validate` (mustering-out tables must cover every row a character in
that career can roll). Rebuilding the skill vocabulary also breaks `background-skills.toml`,
which grants eleven of the removed names, so that table is retargeted and reconciled against the
source in the same pass (FR-014a). Career selection draws from the whole pool, so tripling it
changes what every seed produces; that, the corrected background skills, and the extra draw each
cascade level costs ship together as one flagged breaking change with no compatibility path.

Technical approach: career schema rises to version 4, the skills registry to version 2, both as
minimal changes to shapes that already exist. Sixteen new career files and three renames land in
`src/cetools/data/careers/`. The coverage check is a cross-file rule in `rules.py`, because it
needs `chargen-parameters.toml`'s row modifiers alongside each career's own ladders. Structural
work (fixture re-pin, renames) is committed before any behavioral work, per Tidy First.

## Technical Context

**Language/Version**: Python 3.13+ (floor set by the constitution; the working interpreter is
3.14)

**Primary Dependencies**: standard library only for the engine (`tomllib`, `importlib.resources`);
Typer for the CLI, already present. This feature adds no runtime dependency.

**Storage**: TOML rules-data files shipped inside the package under `src/cetools/data/`. No
database, no runtime writes.

**Testing**: pytest, run as `uv run pytest`. Existing suite: 1253 tests, green at the branch
point.

**Target Platform**: cross-platform CLI and importable library; no platform-specific code.

**Project Type**: single project (library plus thin CLI), the layout established by features
001 through 003.

**Performance Goals**: none beyond "a batch of characters is instant". Career count triples,
which touches only in-memory dict sizes and a load-time validation loop.

**Constraints**:

- Every draw comes from the seeded `Roller`; the ship-share quantity and each cascade step are
  draws, so both must be seeded and neither may consult the clock or `random`.
- New SRD-derived data files are Open Game Content: OGC header comment, under
  `src/cetools/data/careers/`, and never containing the strings "Cepheus Engine" or
  "Samardan Press".
- Human-readable CLI output is pinned in `README.md` and `tests/golden/`; `--json` output is
  pinned in `tests/contract/`.
- Structural and behavioral changes never share a commit.

**Scale/Scope**: 24 career files (8 reconciled, 16 added, 3 renamed), 2 registry files rebuilt,
1 draft table updated, 1 background-skills table retargeted and reconciled (FR-014a), 1 new
validation rule, 2 schema-version bumps, 1 notation form added, 24 committed verification
artifacts plus a completeness index, a roster-level record, and a background-skills record
(FR-023a, FR-023b).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Assessment | Verdict |
|---|---|---|
| I. Library-First | Every change is in `src/cetools/` library modules and shipped data. The CLI gains no game logic; the new coverage check surfaces through the existing `validate` command and the existing `ValidationProblem` shape. | PASS |
| II. CLI Text I/O Protocol | No new command, no new flag. The new problem class flows through the existing human-readable and `--json` renderings of `ValidationReport`. Exit codes unchanged. | PASS |
| III. Test-First | Every behavior below is written as a failing test first, one at a time, with the full suite run after each step. Tasks are ordered so the test precedes the implementation in every case. | PASS |
| IV. Seed-Reproducible | Two new draws are introduced (the ship-share quantity, and each additional cascade step). Both come from the walk's `Roller`. Nothing reads the clock. The *values* a seed produces change, which is a breaking change, not a violation: reproducibility is a promise within one package version. | PASS |
| V. Data-Driven Rules Content | All twenty-four careers, both vocabularies, and the ship-share dice live in TOML. The coverage check reads its row modifiers from `chargen-parameters.toml` rather than holding a constant. No table content enters engine code. | PASS |
| VI. Simplicity | The skills registry file shape is unchanged; only its resolution semantics deepen. The notation gains exactly one production. The rank title becomes optional rather than gaining a parallel representation. No new module, no new abstraction layer. | PASS |

Licensing gate: the sixteen new career files are SRD-derived and therefore OGC, carrying the
same header comment the existing eight carry, in the directory the README licensing section and
the Section 15 game-data notice already designate. The twenty-four verification artifacts under
`specs/004-complete-srd-careers/verification/` reproduce source table values for the record;
they are not shipped in the sdist or wheel, but they carry the same OGC header comment so their
provenance is not ambiguous to a reader of the repository.

No entries in Complexity Tracking: nothing here exceeds the simplest adequate solution.

**Post-design re-check (after Phase 1)**: still PASS on all six, with two points worth naming.
The Phase 1 design keeps `SkillReference` and the whole JSON contract unchanged, so the nested
cascade costs no new type and no contract change (VI). The quantified benefit adds one dataclass
and one grammar production, and confines its effect to the roll: the sheet still holds plain
item names, so the renderer and the JSON contract are untouched (II, VI). Nothing in the design
moved rules content into engine code (V), and both new draws come from the walk's `Roller` (IV).

## Project Structure

### Documentation (this feature)

```text
specs/004-complete-srd-careers/
├── plan.md              # This file
├── research.md          # Phase 0: the roster, both vocabularies, the audit, the decisions
├── data-model.md        # Phase 1: schema v4, registry v2, the coverage invariant
├── quickstart.md        # Phase 1: runnable validation scenarios
├── contracts/
│   ├── data-files.md    # Career schema v4 and skills registry v2, as a delta on 003
│   └── notation.md      # The dice-quantity benefit form, as a delta on 002
├── checklists/
│   └── requirements.md  # Already present
├── verification/        # Implementation output (FR-023a): one file per career, 24 total
└── tasks.md             # Phase 2 output (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
src/cetools/
├── notation.py          # + the dice-quantity benefit form (QuantifiedBenefit)
├── registries.py        # + nested-cascade resolution in SkillRegistry
├── careers.py           # + optional rank title, quantified benefit, re-enlistment field removal
├── rules.py             # + schema-version table bumps, + the mustering-out coverage rule
├── generator.py         # + recursive cascade resolution, + ship-share quantity draw
└── data/
    ├── careers/         # 8 reconciled, 16 added, 3 renamed to long-form basenames
    ├── chargen/
    │   ├── draft.toml   # The three long career names
    │   └── background-skills.toml  # Retargeted onto the rebuilt vocabulary (FR-014a)
    └── registries/
        ├── skills.toml  # Rebuilt to the source vocabulary, schema-version 2
        └── benefits.toml# Rebuilt to the source vocabulary

tests/
├── contract/            # --json shape, unchanged in shape; fixture counts touched
├── golden/              # npc_*.txt render fixtures re-pinned (structural, first)
├── guards/              # packaging and licensing guards, unchanged
├── integration/         # + 24 traversal walks, + coverage-rule rejection cases
├── property/
└── unit/                # + notation, registry, career-parse, rules-check cases
```

**Structure Decision**: the single-project layout already in place. This feature adds no
directory and moves no module; it edits five engine modules, rewrites two registry data files,
and grows the `careers/` data directory from eight files to twenty-four.

## Commit ordering (Tidy First)

Structural first, each its own commit, each with the full suite green before and after:

1. **`refactor(golden): re-pin the render fixtures onto source-legal names`**. The hand-built
   `Character` literals in `tests/unit/test_render_character.py` and their committed
   `tests/golden/npc_*.txt` counterparts carry names no source vocabulary defines (`Pilot`,
   `Vehicle (Grav)`, `Gambler`, `Mechanic`, `Flyer`, `Personal Vehicle`). They are fixtures, not
   generated output, so re-pinning them changes no engine behavior; doing it now keeps the one
   later regeneration attributable entirely to the enlarged pool (FR-030, SC-006).
2. **`refactor(careers): rename the three planetary-defense career files`**. Override
   composition keys on basename, so the rename changes a public composition key and the
   `RulesData.careers` mapping key. Display names do not change here.

Behavioral after, in dependency order: notation form, registry semantics, career schema,
coverage rule, vocabularies and the background-skills table they break, career content, draft
table, README regeneration, changelog. The detailed ordering is `/speckit-tasks`'s output.

## Known risks

- **The re-pin step must not become a regeneration.** If a fixture's re-pinned bytes differ from
  what the renderer emits for that fixture, the step has changed behavior. The suite pins this:
  the goldens are asserted against `as_text` directly.
- **Recursive cascade resolution consumes an extra draw per nesting level**, which shifts every
  subsequent draw in the walk. It is one of several reasons a seed's output changes; the
  changelog entry covers the whole set rather than attributing the shift to the pool alone.
- **`Animals` lists `Survival` among its specialties while `Survival` is also a top-level
  skill.** A character can therefore hold both `Survival-1` and `Animals (Survival)-1` as
  distinct entries. That is what the source says; see research.md D6 for why it is transcribed
  rather than normalized.
- **Four committed tests assert the opposite of what this feature makes true**, and each one
  turns the commit that lands its change red unless it is retired in the same commit. They are
  not incidental fixtures: each was written deliberately against the old rule, so each needs its
  premise inverted rather than its assertion deleted. `tasks.md` names all four in the task that
  breaks them.
  - `tests/unit/test_careers.py::test_a_rank_without_its_title_is_rejected` — `title` becomes
    optional (FR-007).
  - `tests/unit/test_render_character.py::test_no_shipped_ladder_rank_leaves_a_character_untitled`
    — seven shipped careers gain untitled ranks (FR-008).
  - `tests/unit/test_generator.py`'s re-enlistment-characteristic case — the field is removed
    from that throw position (FR-013a).
  - `tests/integration/test_overrides.py`'s override career fixture, which grants `Carouse`,
    `Gambler`, and `Stealth` and asserts the override validates (FR-014).
- **The skills-vocabulary rebuild reaches outside `careers/`.** `background-skills.toml` grants
  eleven of the removed names, and `tests/unit/test_rules_agreement.py` pins that every
  background skill resolves. Retargeting it is FR-014a; reading the source to do so showed two of
  its three lists are a different edition's table (research.md R8), so it is transcribed rather
  than renamed.
