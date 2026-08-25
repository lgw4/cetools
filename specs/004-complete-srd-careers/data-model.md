# Data Model: Complete SRD Careers

This is a delta on the data model established by
[003-npc-generator](../003-npc-generator/data-model.md). Types not mentioned here are unchanged.

## Entities

### Career (`CareerDefinition`, `src/cetools/careers.py`)

Unchanged in fields. What changes is what two of its members admit.

| Field | Type | Change |
|---|---|---|
| `name` | `str` | none in type. Three shipped values change (R2). |
| `medical_tier` | `str` | none |
| `always_available` | `bool` | none |
| `re_enterable` | `bool` | none |
| `throws` | `Mapping[str, Throw]` | `re-enlistment` no longer admits a characteristic |
| `tables` | `Mapping[str, SkillTable]` | none |
| `ladders` | `tuple[RankLadder, ...]` | none |
| `mustering_out` | `MusteringOut` | `benefits` admits a quantified item |

Twenty-four instances in the packaged data set.

### Throw

```python
@dataclass(frozen=True, slots=True)
class Throw:
    characteristic: str | None
    target: int
    dice: str
```

Type unchanged. The `re-enlistment` position now rejects a `characteristic` key as
unrecognized, naming `throws.re-enlistment.characteristic` and the keys the position admits.
`characteristic` stays optional in the type because the field still exists for the four throws
that use it, and because a re-enlistment `Throw` continues to carry `None`.

**Validation rule**: `throws.re-enlistment` admits exactly `target` and `dice`. The other four
throw positions admit `characteristic`, `target`, and `dice` as before.

### Rank

```python
@dataclass(frozen=True, slots=True)
class Rank:
    rank: int
    title: str = ""
    bonus: SkillTableEntry | None = None
```

`title` becomes optional in the file and defaults to the empty string. All four combinations are
now representable, and all four occur in the source:

| Title | Bonus | Occurs in |
|---|---|---|
| present | present | Navy rank 0 (`Starman`, `Zero-G 1`), and every career's rank rows that print a bracketed grant beside a title |
| present | absent | most rank rows 1 through 6 |
| absent | present | the six commissionless careers' rank 0 (Athlete, Barbarian, Belter, Entertainer, Hunter, Scout) |
| absent | absent | Drifter rank 0, the one row the source prints entirely empty |

**Validation rules**:

- `rank` is a non-negative integer, distinct within its ladder (unchanged).
- `title`, when present, is a non-empty string. An explicit `title = ""` is rejected: absence is
  written by omitting the key, not by writing an empty value (FR-013).
- A rank with neither a title nor a bonus is valid. The entry ladder must still carry a rank 0,
  because the walk grants that row's bonus unconditionally on entering a career; a rank 0 with
  no bonus grants nothing, which `_grant_rank_bonus` already handles.

### MusteringOut

```python
@dataclass(frozen=True, slots=True)
class MusteringOut:
    cash: tuple[int, ...]
    benefits: tuple[BenefitItem | QuantifiedBenefit | CharacteristicAdjustment, ...]
```

**Validation rules**:

- `cash` is a non-empty array of non-negative integers (unchanged). Zero is a real value: it is
  Barbarian's and Drifter's row 1.
- `benefits` is a non-empty array (unchanged), each entry a bare benefit item, a characteristic
  adjustment, or a quantified benefit.
- Neither table has a fixed length. Both are bounded below by the coverage rule below, and by
  nothing above.

### QuantifiedBenefit (new, `src/cetools/notation.py`)

```python
@dataclass(frozen=True, slots=True)
class QuantifiedBenefit:
    dice: str
    name: str
```

A material-benefit row awarding a rolled number of one item. Admissible only in
`EntryContext.BENEFIT_TABLE`. `dice` is checked by `_check_dice`, which rejects `d66`; `name` is
resolved against the benefits registry exactly as a `BenefitItem` is.

Six instances in the packaged data, all `1d6 Ship Share` (R6).

### SkillRegistry (`src/cetools/registries.py`)

```python
@dataclass(frozen=True, slots=True)
class SkillRegistry:
    skills: Mapping[str, tuple[str, ...]]
```

Type unchanged; the graph it describes deepens. A specialty is now permitted to name another
entry that itself has specialties, which makes it a nested cascade.

**Resolution** (`resolve`, used for validation) is unchanged in its four outcomes: a reference
naming a skill and, optionally, one of that skill's declared specialties is `VALID`. Nesting
does not change what a *written* reference may say: `Vehicle (Aircraft)` is valid because
`Aircraft` is one of `Vehicle`'s specialties, and `Aircraft (Winged Aircraft)` is valid because
`Winged Aircraft` is one of `Aircraft`'s.

**Generation-time resolution** (`_resolve_specialty`, `src/cetools/generator.py`) becomes a loop
rather than a single draw. Given a reference with no specialty:

1. Look up the name's specialties. If there are none, the reference is terminal; return it.
2. Draw one specialty uniformly from the seeded roller.
3. If that specialty is itself an entry with specialties, replace the name with it and go to 1.
4. Otherwise return `SkillReference(name, specialty)`.

Each nesting level costs one draw. Under the packaged data the loop runs twice at most, for
`Vehicle` resolving into `Aircraft` or `Watercraft`.

**Validation rules**:

- A skill name contains no parentheses (unchanged).
- A specialty is a string (unchanged).
- The specialty graph is acyclic. A chain that revisits a name is reported against
  `skills.<name>` naming the cycle, because generation-time resolution would otherwise not
  terminate.

Seventy entries in the packaged registry (R4): the 68 the skill chapter defines, plus
`Perception` and `Prospecting`, which career tables grant and the chapter never defines. The
registry file records that discrepancy against those two names (FR-016).

### BenefitRegistry

Type unchanged. Eight entries (R5): `Low Passage`, `Mid Passage`, `High Passage`, `Weapon`,
`Explorers' Society`, `Ship Share`, `Courier Vessel`, `Research Vessel`.

### Character-facing types

`Character`, `CareerService`, `CharacterSkill`, and the JSON document shape are unchanged.
Specifically:

- `CareerService.title` and `Character.title` stay `str` and carry `""` for an untitled rank
  (FR-009). The Universal Character Format already omits an empty title and its separator.
- `Character.benefits` stays `tuple[str, ...]`. A rolled quantity of *n* ship shares appends the
  name *n* times, so the human-readable renderer's existing repeat collapsing prints
  `Ship Share (x3)` and the JSON `benefits` array holds three identical strings (FR-011).

## Cross-file invariants (`src/cetools/rules.py`)

Existing rules are unchanged. One is added.

### Mustering-out coverage (FR-020, FR-021)

For each career in force, with `roll` the parsed `chargen.mustering-out.roll`:

```text
max_total          = roll.count * roll.sides + roll.modifier
highest_rank       = max(rank.rank for ladder in career.ladders for rank in ladder.ranks)
cash_required      = max_total + chargen.mustering-out.retired-cash-dm
material_required  = max_total + highest_matching(chargen.mustering-out.material-rank-dm, highest_rank)
```

- `len(career.mustering_out.cash) >= cash_required`, else a problem at
  `mustering-out.cash` reporting the row count found against the row count required.
- `len(career.mustering_out.benefits) >= material_required`, else the same at
  `mustering-out.benefits`.

`highest_matching` is the existing "highest-ranked row at or below this rank, not cumulative"
rule the walk already uses for both rank tables.

The retirement modifier is unconditional because the pension is a property of the character's
total terms, not of the career's ranks, so every cash table is bounded by `max_total +
retired-cash-dm`. The material modifier is rank-conditioned, so a career whose ladders stop at
rank 0 is bounded by `max_total` alone.

Under the packaged data: `max_total` is 6, `retired-cash-dm` is 1, and `material-rank-dm` is 1
at rank 5. Every cash table therefore needs 7 rows, the seventeen careers whose ladders reach
rank 5 need 7 material rows, and the seven that stop at rank 0 need 6. That is exactly what the
source prints.

The rule is stated over the careers *in force*, so an override career file is subject to it
(FR-021), and its bound is computed from that file's own ladders rather than from a constant.

## Schema versions

| Kind | Was | Becomes | Why |
|---|---|---|---|
| `career` | 3 | 4 | optional rank title, quantified benefit entry, re-enlistment characteristic removed |
| `skills` | 1 | 2 | a specialty may name a cascade, and resolution continues through it |
| `benefits` | 1 | 1 | contents change; shape does not |
| `draft-table` | 1 | 1 | contents change; shape does not |
| everything else | | unchanged | |

`rules._SUPPORTED_VERSION` carries both bumps. A file declaring the old version is rejected on
its header with the existing message, which is the intended way an override author learns the
shape moved.

## Verification artifacts (FR-023a)

`specs/004-complete-srd-careers/verification/<basename>.md`, one per career, twenty-four in all,
plus `index.md` recording which are complete.

Each file is written source-first: for every field, the source's printed value, then the
committed file's value, then a verdict of `match`, `corrected` (the file was changed to match),
or `deviation` (the file keeps a different value, with the reason, which must also appear in the
career file itself under FR-024). The fields enumerated are the ones R1 tabulates plus every
skill-table row, every rank row, and every mustering-out row, together with `medical-tier`,
`always-available`, and `re-enterable` (FR-006a).

These files reproduce source table values, so each carries the same OGC header comment the
shipped career files carry, even though `specs/` is not part of the sdist or wheel.
