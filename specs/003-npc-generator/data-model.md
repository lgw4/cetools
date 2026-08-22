# Phase 1 Data Model: NPC Generator

**Feature**: `003-npc-generator` | **Date**: 2026-08-21

Every type below is a frozen dataclass with `slots=True`, following the convention the two
previous features established. Sequence fields are tuples and mapping fields are read-only
mappings, so a caller holding a character cannot edit it underneath another caller.

**Vocabulary.** The spec says "character", "generation history", "career service", "term",
"mishap", "debt", "benefit item", "universal chargen table", "career definition", "name
table", and "Universal Character Format". The code says `Character`, `HistoryStep`,
`CareerService`, the term loop, the mishap table, `Character.debt`, `Character.benefits`,
the six chargen types, `CareerDefinition`, `GivenNameTable` / `SurnameTable`, and the
`as_text` registration for `Character`. The mapping is one-to-one. `CharacterBatch` is the
one term the code adds, and the spec's word for it is "batch".

## Overview

```text
CharacterBatch
├── seed        : int                        the master seed a referee quotes
├── provenance  : Provenance                 version and overrides, from RulesData
└── characters  : tuple[Character, ...]      one per position, a tuple of one for a single run

Character
├── seed             : int                   the derived seed that reproduces this one person
├── name             : str                   always present; what every rendering writes
├── given_name       : str                   "" when the caller supplied the name
├── surname          : str                   ""
├── surname_region   : str                   ""
├── title            : str                   rank title attached to the rendered name; "" if none
├── characteristics  : Mapping[str, int]     in the characteristics registry's order
├── skills           : tuple[CharacterSkill, ...]
├── careers          : tuple[CareerService, ...]   in the order entered
├── age              : int
├── funds            : int                   never negative
├── debt             : int                   never negative; separate from funds
├── pension          : int                   annual amount; 0 if none
├── benefits         : tuple[str, ...]       named items, in the order received
└── history          : tuple[HistoryStep, ...]
```

## The produced value (`cetools/character.py`)

### `Character`

| Field | Type | Notes |
|---|---|---|
| `seed` | `int` | The walk seed. Quoted back to `--seed` it regenerates this character alone (FR-050a, research R2). |
| `name` | `str` | Always non-empty, always what renders (FR-047d). The rank title is **not** part of it; the renderer joins the two. |
| `given_name` | `str` | The rolled given name, or `""` when the caller supplied the name. |
| `surname` | `str` | The rolled surname, or `""`. |
| `surname_region` | `str` | The region the surname table declared, or `""`. Recorded so SC-019's weighting check reads a field rather than splitting rendered text. |
| `title` | `str` | The rank title from the most recently served career whose ladder names one for the rank held (FR-047c). `""` when no career titled them. |
| `characteristics` | `Mapping[str, int]` | Keyed by registry code, in the registry's file order, which is the order the UPP renders in. Every value is within the pseudo-hex range (research R13). |
| `skills` | `tuple[CharacterSkill, ...]` | Unsorted here; the renderer sorts. Held in acquisition order so the history and the sheet can be reconciled. |
| `careers` | `tuple[CareerService, ...]` | At least one. In the order entered. |
| `age` | `int` | Starting age plus the years each term cost, by how it ended. |
| `funds` | `int` | Mustering-out cash after debt was settled from it. Never negative (FR-025). |
| `debt` | `int` | What proceeds did not cover (FR-026). Never negative. Distinct from funds so a character never has a negative balance. |
| `pension` | `int` | The annual amount, or 0. Carried distinctly from funds because it is an ongoing amount rather than a balance (FR-018). |
| `benefits` | `tuple[str, ...]` | Material benefits as names and nothing more (FR-027). Repeats are kept as repeats; the renderer collapses them. |
| `history` | `tuple[HistoryStep, ...]` | Non-empty. Every number on the sheet traces to a step in it (FR-030). |

`funds` and `debt` are never both reduced below zero, and a mustering-out payment settles
debt before funds are recorded, which is what makes `funds >= 0 and debt >= 0` an invariant
rather than a convention (SC-004).

### `CharacterSkill`

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | The parent skill's name as the registry spells it. |
| `specialty` | `str \| None` | `None` means the parent itself, which at level 0 is a skill the character has without a specialty chosen. |
| `level` | `int` | Non-negative. Level 0 is shown on the sheet (FR-045). |

Three flat fields rather than a nested `SkillReference` plus a level, because that is how
the value serializes (`name`, `specialty`, `level`) and a nesting nothing reads is
structure for its own sake. It is deliberately **not** `SkillGrant`, which has the same
shape: a grant is an instruction written in a table and a `CharacterSkill` is a fact about a
person, and the two diverge the moment either grows a field.

A parent at level 0 and a specialty at level 1 coexist as two entries. Both render.

### `CareerService`

| Field | Type | Notes |
|---|---|---|
| `career` | `str` | The career's declared name, which is what the sheet writes. |
| `terms` | `int` | At least one. Counts mishap-ended terms (FR-020). |
| `ladder` | `str` | The ladder the character was on when the service ended. |
| `rank` | `int` | The rank reached on that ladder. |
| `title` | `str` | The ladder's title for that rank, or `""` when it names none. |
| `commissioned` | `bool` | Whether a commission was entered. A commission is entered once per career (spec Edge Cases). |
| `entered_by` | `str` | `"selected"`, `"drafted"`, or `"fallback"`. What FR-004 and FR-006 require recorded. |
| `ended` | `str` | `"mishap"`, `"re-enlistment"`, `"chose to leave"`, or `"term cap"`. |
| `benefit_rolls` | `int` | Taken at mustering out. SC-004 audits it against `terms` and `rank`. |

`entered_by` and `ended` are also history steps. They are carried here as well because
SC-004's audit reads the character's own fields and would otherwise have to reconstruct
each service by scanning the history for its boundaries.

### The generation history

FR-030a requires each step to be a structured record whose parts are separately
addressable, and forbids recording a step only as a line of prose. The fuller text
rendering composes its line from these parts; machine-readable output emits the parts
themselves.

#### `HistoryStep`

| Field | Type | Notes |
|---|---|---|
| `kind` | `str` | Which kind of step. The closed set is below. |
| `career` | `str` | `""` where the step falls outside a career. |
| `term` | `int` | `0` where the step falls outside a term. |
| `throw` | `StepThrow \| None` | `None` for a step that decided rather than threw. |
| `selected` | `str` | What was chosen at random: a career name, a table name, a specialty, a characteristic. `""` where nothing was chosen. |
| `effects` | `tuple[StepEffect, ...]` | What followed. Possibly empty, for a step whose only outcome was the throw's own success. |

Step kinds, closed: `characteristics`, `background-skills`, `career-selected`,
`qualification`, `draft`, `career-entered`, `basic-training`, `rank-bonus`, `survival`,
`mishap`, `injury`, `commission`, `advancement`, `skill-roll`, `aging`, `continuation`,
`re-enlistment`, `career-ended`, `mustering-out`, `benefit`, `medical-bills`,
`debt-settled`, `pension`.

The set is closed for the same reason the career schema's table names are: an open set
makes a misspelled kind a new kind rather than a typo, and SC-005's automated traceability
check groups by it.

#### `StepThrow`

| Field | Type | Notes |
|---|---|---|
| `faces` | `tuple[int, ...]` | As rolled. |
| `modifiers` | `tuple[Modifier, ...]` | Itemized, reusing `tasks.Modifier`. This is what tells a wrong engine from interesting dice. |
| `total` | `int` | `sum(faces)` plus the modifiers. |
| `target` | `int` | |
| `success` | `bool` | `total >= target`. |

Deliberately not `CheckResult`, which carries provenance and is a task resolution rather
than a lifepath throw. A lighter record with the same arithmetic keeps the two from being
confused, and keeps a character from carrying the provenance of its own rules data once per
throw.

A table-reading roll, where there is no target to beat, carries `target = 0` and
`success = True`, and the row it read is in `selected`. That is the only place the two
fields do not mean what they say, and it is why `selected` exists rather than the outcome
being inferred from the total.

#### `StepEffect`

| Field | Type | Notes |
|---|---|---|
| `kind` | `str` | What moved. The closed set is below. |
| `subject` | `str` | Which one: a characteristic code, a rendered skill, a career name, a benefit item's name. `""` where the effect names nothing. |
| `amount` | `int` | The signed change, or `0` where the effect is not numeric. |

Effect kinds, closed: `characteristic`, `skill`, `credits`, `benefit`, `debt`, `pension`,
`age`, `rank`, `commission`, `career`, `benefit-roll-forfeit`.

A characteristic reduction floored at the bottom of the declared pseudo-hex range records
two effects: the reduction the rule called for, and the amount actually applied, when they
differ (research R13). SC-005 reads both.

Three fields rather than a payload per kind, because SC-004 and SC-005 are automated audits
that group and sum over the whole history, and a union of eleven shapes would make the
audit a dispatch. The cost is that `amount` means nothing for `commission`, which the
contract states.

### `CharacterBatch`

| Field | Type | Notes |
|---|---|---|
| `seed` | `int` | The master seed. Position 0's character carries the same value (research R2). |
| `provenance` | `Provenance` | Copied from the `RulesData` the batch was generated against. |
| `characters` | `tuple[Character, ...]` | Non-empty. A tuple of one for a single-character run, which is what makes FR-050a's one shape hold. |

## The universal chargen tables (`cetools/chargen.py`)

Each is built by its own parse function from its own file, exactly as the registries are.
Every one of them is a single-instance kind.

### `DraftTable`

| Field | Type | Notes |
|---|---|---|
| `roll` | `str` | Dice notation. The row read is the total, and row order is significant because the die is positional (FR-005). |
| `careers` | `tuple[str, ...]` | One career name per row, in row order. Every one must resolve to a career in force, checked as a cross-file rule. |

### `AgingTable`

| Field | Type | Notes |
|---|---|---|
| `roll` | `str` | Dice notation. |
| `rows` | `tuple[AgingRow, ...]` | Sorted by `minimum`. Exactly one row is unbounded above, and the lowest row is a floor: a modified result beneath it reads that row. |

| `AgingRow` field | Type | Notes |
|---|---|---|
| `minimum` | `int` | May be negative. |
| `maximum` | `int \| None` | `None` for the single unbounded top row. |
| `effects` | `tuple[ClassEffect, ...]` | What the row does. |

| `ClassEffect` field | Type | Notes |
|---|---|---|
| `characteristic_class` | `str` | A class declared in the characteristics registry (research R12). |
| `count` | `int` | How many distinct characteristics of that class are reduced. |
| `amount` | `int` | Signed. The generator selects which characteristics at random and records the choice. |

`ClassEffect` is what lets "reduce three physical characteristics by 2, reduce one mental
characteristic by 1" be one row of data rather than a branch in the engine.

### `MishapTable`

| Field | Type | Notes |
|---|---|---|
| `roll` | `str` | Dice notation. |
| `rows` | `tuple[MishapRow, ...]` | Indexed by the total, in row order. |
| `injury_roll` | `str` | Dice notation for the injury table two rows defer to. |
| `injuries` | `tuple[InjuryRow, ...]` | The injury table, held here because nothing but a mishap reaches it. |

| `MishapRow` / `InjuryRow` field | Type | Notes |
|---|---|---|
| `description` | `str` | Rendered in the history's fuller line, never parsed. |
| `effects` | `tuple[MishapEffect, ...]` | Structured, so the audit reads them. |

| `MishapEffect` field | Type | Notes |
|---|---|---|
| `kind` | `str` | One of `characteristic-class`, `debt`, `years`, `forfeit-term-benefit`, `forfeit-career-benefits`, `roll-injury`. |
| `characteristic_class` | `str` | For `characteristic-class`; `""` otherwise. |
| `count` | `int` | How many characteristics; `0` where not applicable. |
| `amount` | `str` | Dice notation or a plain integer as text. A characteristic reduction may be `1d6` and a debt may be `10000`, so the field admits both and the parser types it. |

### `BackgroundSkills`

| Field | Type | Notes |
|---|---|---|
| `law_level` | `tuple[SkillGrant, ...]` | The homeworld law-level list. |
| `trade_code` | `tuple[SkillGrant, ...]` | The homeworld trade-code list. |
| `education` | `tuple[SkillGrant, ...]` | The education list. |

Entries are notation, in the skill-table context, so `Gun Combat 0` resolves through the
skills registry like every other table entry. The homeworld draw is uniform over the
concatenation of `law_level` and `trade_code`; duplicates across those two lists are
meaningful weighting and are preserved (research R5).

### `MedicalTiers`

| Field | Type | Notes |
|---|---|---|
| `roll` | `str` | Dice notation. |
| `rank_dm` | `bool` | Whether the character's rank is added as a modifier. |
| `tiers` | `Mapping[str, tuple[MedicalThreshold, ...]]` | Keyed by tier name, thresholds sorted descending so the first match wins. |

| `MedicalThreshold` field | Type | Notes |
|---|---|---|
| `target` | `int` | The modified result must equal or exceed it. |
| `paid_percent` | `int` | 0 to 100. What the employer pays. |

A modified result below every threshold pays nothing, which is stated in the file rather
than assumed by the engine.

### `ChargenParameters`

Every scalar the walk depends on. The full key list is in `contracts/data-files.md`; the
type exposes them as named attributes so a misspelling is an `AttributeError` at import
rather than a `KeyError` mid-walk. Grouped as: the characteristic roll; the background
skill count rule; the term parameters (starting age, term years, mishap term years, cap,
the age aging begins at); qualification (penalty per previous career, draft entries
allowed); basic training; survival's natural failure; the skill-roll counts; the commission
restriction; the continuation throw; mustering out (roll, cash cap, retired cash modifier,
rank benefit bonuses, material rank modifier); the pension; and the medical costs.

## The name tables (`cetools/names.py`)

### `GivenNameTable`

| Field | Type | Notes |
|---|---|---|
| `source` | `str` | Where the entries were drawn from (FR-043e). Non-empty. |
| `names` | `tuple[str, ...]` | Non-empty (FR-043h). No gender field exists anywhere in the schema (FR-043b). |

### `SurnameTable`

| Field | Type | Notes |
|---|---|---|
| `region` | `str` | Distinct across the tables in force, checked as a cross-file rule. |
| `source` | `str` | Non-empty (FR-043e). |
| `names` | `tuple[SurnameEntry, ...]` | Non-empty (FR-043h). |

| `SurnameEntry` field | Type | Notes |
|---|---|---|
| `name` | `str` | Non-empty. |
| `people` | `str` | The people the name comes from. Required by FR-043d for the indigenous-peoples table, optional in the schema, and asserted for that shipped file by SC-015b. Optional rather than required because an override adding a region has no such obligation. |

### `Name`

What a roll produces. Not stored on the character, which carries the four fields flat.

| Field | Type | Notes |
|---|---|---|
| `given_name` | `str` | |
| `surname` | `str` | |
| `region` | `str` | |
| `full` | `str` | `f"{given_name} {surname}"`, composed and never reordered (FR-047a). |

`roll_name(roller, given, surnames)` selects a region uniformly over the surname tables in
force, then a surname uniformly within it (FR-043f), and a given name uniformly. Weighting
over tables rather than over names is what makes an override adding an eighth region give
it the same weight as each of the others, and what SC-019's deliberately unequal shipped
table sizes exist to prove.

## Changes to existing types

### `CharacteristicRegistry` gains three things

| Field | Type | Notes |
|---|---|---|
| `names` | `Mapping[str, str]` | Unchanged: code to label, in file order. |
| `classes` | `Mapping[str, str]` | Code to class, `"physical"` or `"mental"` as the file declares (research R12). |
| `bands` | `tuple[Band, ...]` | Moved from `TaskParameters` (FR-039). Sorted by `minimum`, exactly one unbounded. |
| `pseudo_hex_minimum` | `int` | The lowest score the symbols cover. |
| `pseudo_hex` | `tuple[str, ...]` | `pseudo_hex[score - pseudo_hex_minimum]` is the symbol. |

| Method | Returns |
|---|---|
| `characteristic_dm(score)` | The band's modifier. Moved verbatim from `TaskParameters`. |
| `symbol(score)` | The pseudo-hex symbol, raising `RulesDataError` naming the score and the range when it is outside. |
| `floor()` | `pseudo_hex_minimum`, the value a reduction clamps at (research R13). |

`Band` moves from `tasks.py` to `registries.py` with it. `__all__` is unchanged, because the
name is re-exported either way.

### `TaskParameters` loses two things

`characteristic_bands` and `characteristic_dm` are gone; `check` reads
`rules.characteristics.characteristic_dm(...)`. `roll`, `target`, `unskilled_dm`,
`difficulty_dms`, `difficulty_dm`, and `default_difficulty` are untouched. This is a
breaking library change and no task check result may change as a consequence (SC-014).

### `CareerDefinition` gains four things and changes two

| Field | Type | Notes |
|---|---|---|
| `medical_tier` | `str` | A tier name in the medical-tiers file, checked as a cross-file rule (FR-034). |
| `always_available` | `bool` | Marks the career reachable as the qualification fallback (FR-006). Default `false`. |
| `re_enterable` | `bool` | Marks the career available again after being left (FR-015). Default `false`. |
| `throws` | `Mapping[str, Throw]` | `promotion` becomes optional. Together with an absent `commission` that is what FR-009 reads as two skill rolls a term. |
| `tables` | `Mapping[str, SkillTable]` | `advanced` is renamed `specialist`; `advanced-education` becomes required and keeps declaring its own gate in the file. |
| `ladders` | `tuple[Ladder, ...]` | Each gains a `role` of `"entry"` or `"commissioned"` (FR-007b). Exactly one is `entry`; a career declaring a commission throw declares exactly one `commissioned`, and a successful commission moves the character to it at the lowest rank it declares. |
| `mustering_out`, `name` | unchanged | |

Renaming `advanced` to `specialist` follows the source material's own heading and removes
the collision with `advanced-education`, which two adjacent keys differing by a suffix made
easy to transpose.

### `RulesData` gains eight fields

```text
RulesData
├── task_parameters   : TaskParameters
├── characteristics   : CharacteristicRegistry
├── skills            : SkillRegistry
├── benefits          : BenefitRegistry
├── careers           : Mapping[str, CareerDefinition]
├── draft             : DraftTable                       NEW
├── aging             : AgingTable                       NEW
├── mishaps           : MishapTable                      NEW
├── background_skills : BackgroundSkills                 NEW
├── medical_tiers     : MedicalTiers                     NEW
├── chargen           : ChargenParameters                NEW
├── given_names       : GivenNameTable                   NEW
├── surnames          : Mapping[str, SurnameTable]       NEW, keyed by file stem
└── provenance        : Provenance
```

`surnames` is the second repeatable kind, alongside `careers`. Everything else added is a
single-instance kind, taking `_SINGLETON_KINDS` from four to eleven, which is why the
per-kind dispatch in `rules._validate` becomes a table before the kinds are added rather
than after.

### Cross-file rules this feature adds

Checked after every file has been read, alongside the two the previous feature has.

| Rule | Requirement |
|---|---|
| Every career the draft table names resolves to a career in force | FR-005. The run fails before any character is produced, naming the unresolvable career, rather than falling back to Drifter. |
| Every career's `medical-tier` names a tier in the medical-tiers file | FR-034. |
| No two surname tables in force declare the same region | FR-043c, and the analogue of the duplicate-career-name rule. The problem names both files. |
| At least one surname table is in force | FR-043f weights over the tables in force, and no tables in force means no surname can be drawn. |
| Every skill any shipped table can grant resolves against the skills registry | FR-040, which is the existing per-entry rule reaching the new tables. |
| Every characteristic class any table in force names is declared in the characteristics registry | FR-040a. An effect naming a class nothing declares reduces nothing, silently. |
| Every career declares exactly one `entry` ladder, and a career declaring a commission throw declares exactly one `commissioned` ladder | FR-007b. |

## Schema versions

| Kind | `schema` value | Version | File |
|---|---|---|---|
| Task parameters | `task-parameters` | **2** | `tasks.toml` |
| Characteristics | `characteristics` | **2** | `registries/characteristics.toml` |
| Skills | `skills` | 1 | `registries/skills.toml` |
| Benefit items | `benefits` | 1 | `registries/benefits.toml` |
| Career | `career` | **2** | `careers/*.toml` |
| Draft table | `draft-table` | 1 | `chargen/draft.toml` |
| Aging table | `aging-table` | 1 | `chargen/aging.toml` |
| Mishap table | `mishap-table` | 1 | `chargen/mishaps.toml` |
| Background skills | `background-skills` | 1 | `chargen/background-skills.toml` |
| Medical tiers | `medical-tiers` | 1 | `chargen/medical-tiers.toml` |
| Chargen parameters | `chargen-parameters` | 1 | `chargen/chargen-parameters.toml` |
| Given names | `given-names` | 1 | `names/given-names.toml` |
| Surnames | `surnames` | 1 | `names/surnames-*.toml` |

Three versions rise and two do not. `skills` and `benefits` gain content and no shape, so a
user file of either kind written against the previous feature stays valid, which is exactly
what per-kind versioning exists for (FR-036). `career` rises because its shape changes in
four ways; `task-parameters` and `characteristics` rise because the modifier bands move
between them (FR-039).
