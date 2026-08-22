# Contract: Rules Data Files

**Feature**: `003-npc-generator`

Extends `002-rules-data-loading/contracts/data-files.md`. Everything that contract states
about headers, composition, basename keying, overrides, and failure still holds unchanged
and is not restated. Only what this feature adds or changes is given here.

## Packaged layout

```text
src/cetools/data/
├── __init__.py                          # GPL-3.0 code, not a data file
├── tasks.toml                           # task-parameters, v2
├── registries/
│   ├── characteristics.toml             # characteristics, v2
│   ├── skills.toml                      # skills, v1
│   └── benefits.toml                    # benefits, v1
├── chargen/                             # NEW
│   ├── draft.toml                       # draft-table
│   ├── aging.toml                       # aging-table
│   ├── mishaps.toml                     # mishap-table
│   ├── background-skills.toml           # background-skills
│   ├── medical-tiers.toml               # medical-tiers
│   └── chargen-parameters.toml          # chargen-parameters
├── names/                               # NEW, and not Open Game Content
│   ├── given-names.toml                 # given-names
│   ├── surnames-africa.toml             # surnames
│   ├── surnames-asia.toml
│   ├── surnames-central-america.toml
│   ├── surnames-europe.toml
│   ├── surnames-indigenous.toml
│   ├── surnames-north-america.toml
│   └── surnames-south-america.toml
└── careers/
    ├── aerospace-defense.toml           # career, v2
    ├── drifter.toml
    ├── marine.toml
    ├── maritime-defense.toml
    ├── merchant.toml
    ├── navy.toml
    ├── scout.toml
    └── surface-defense.toml
```

Twenty-six files. Basenames stay unique across the whole tree, which is the composition key
and which `tests/guards/test_data_layout.py` enforces. Two of these names were chosen for
that reason and not for readability: the background skills file is not `skills.toml`,
because the registry already holds that name, and the chargen scalars file is not
`parameters.toml`, because a later feature adding parameters of another kind would collide
with it.

## Every file: the designation line

This is the one rule in the inherited contract that changes, and it changes because the
name tables are the first shipped data the Open Game Content designation does not reach.

Every **shipped** data file carries exactly one of two designation lines as a header
comment. Carrying both is a failure and carrying neither is a failure (FR-042, SC-015).

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt
```

```toml
# GPL-3.0-only project content; not Open Game Content. See LICENSE.
```

| Designation | Which files | Section 15 |
|---|---|---|
| Open Game Content | Everything derived from the source material: `tasks.toml`, the three registries, the six chargen tables, the eight careers | Must be covered by the game-data notice chain |
| GPL-3.0 | The eight name tables | Must **not** be covered by the notice chain, and must not carry the Open Game Content designation |

Neither designation may appear in a file that is not shipped. An override file is held to
none of this, unchanged from the inherited contract's rule 5: FR-046 of the previous
feature binds what this project redistributes, and a house rule needs no licensing header.

Neither Product Identity string may appear in any shipped data file, whatever its
designation (FR-042).

The Section 15 game-data notice narrows from the whole data tree to the subtrees that hold
Open Game Content, and keeps the machine-readable shape `tests/conftest.py` parses out of
it: parenthesized paths, and the phrase naming the covered extension. See research R9.

## `task-parameters` v2 (`tasks.toml`)

One section is removed and nothing is added.

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "task-parameters"
schema-version = 2

[task]
roll = "2d6"
target = 8
unskilled-dm = -3

[difficulty-dms]
"Average" = 0
# ... one rung per difficulty name
```

`[characteristic-dms]` is **gone**, moved to the characteristics registry (FR-039). A v2
file declaring it is an unrecognized key. Every other key, type, and rule is unchanged, and
no task check result may change as a consequence (SC-014).

## `characteristics` v2 (`registries/characteristics.toml`)

The shape of `[characteristics]` changes from code-to-label to a table per characteristic,
and two sections are added.

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "characteristics"
schema-version = 2

[characteristics.STR]
label = "Strength"
class = "physical"

[characteristics.DEX]
label = "Dexterity"
class = "physical"

[characteristics.END]
label = "Endurance"
class = "physical"

[characteristics.INT]
label = "Intellect"
class = "mental"

[characteristics.EDU]
label = "Education"
class = "mental"

[characteristics.SOC]
label = "Social Standing"
class = "mental"

[modifier-dms]
"0-2" = -2
"3-5" = -1
"6-8" = 0
# ... one row per band, exactly one unbounded

[pseudo-hex]
minimum = 0
symbols = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
           "A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M",
           "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `characteristics.<CODE>.label` | string | yes | Non-empty. The human label. |
| `characteristics.<CODE>.class` | string | yes | A class name. Any string; the shipped data uses `physical` and `mental`. Referenced by the aging and mishap tables (research R12). |
| `modifier-dms.*` | integer | yes, at least one | Keys are `N-M` or `N+`. Exactly one band unbounded. The rules the previous feature enforced on `characteristic-dms`, unchanged. |
| `pseudo-hex.minimum` | integer | yes | The score the first symbol stands for. |
| `pseudo-hex.symbols` | array of string | yes | Non-empty. `symbols[score - minimum]` is the symbol for that score. Each entry non-empty. |

The registry's insertion order is the order the profile renders in, so which characteristics
exist and what order they print in are both data (FR-002).

The declared range is `minimum` through `minimum + len(symbols) - 1`. A characteristic
reduction floors at `minimum` (research R13); a score above the top fails the run naming the
score and the range.

## `skills` v1 (`registries/skills.toml`)

Schema unchanged. Content grows to cover every skill the new tables can grant and every
specialty the cascade rule may choose among (FR-040): the fifteen education skills, the
homeworld skills the law-level and trade-code lists name, and the skills the seven new
careers use. Specialty lists are one level deep, unchanged; nested cascades are not modeled
(research R11).

## `benefits` v1 (`registries/benefits.toml`)

Schema unchanged. Content grows to cover every material benefit the eight careers' tables
name.

## `career` v2 (`careers/*.toml`)

Four changes, and everything else is unchanged from v1.

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "career"
schema-version = 2

name = "Drifter"
medical-tier = "fringe"
always-available = true
re-enterable = true

[throws.qualification]
characteristic = "DEX"
target = 5

[throws.survival]
characteristic = "END"
target = 5

[throws.re-enlistment]
target = 5

# no [throws.commission] and no [throws.promotion]:
# that absence is what grants two skill rolls a term (FR-009)

[tables.personal]
entries = [ ... ]

[tables.service]
entries = [ ... ]

[tables.specialist]
entries = [ ... ]

[tables.advanced-education]
requires = "EDU 8+"
entries = [ ... ]

[[ladders]]
name = "drifter"
role = "entry"
ranks = [
  { rank = 0, title = "Drifter" },
]

[mustering-out]
cash = [ ... ]
benefits = [ ... ]
```

| Location | Type | Required | Change |
|---|---|---|---|
| `medical-tier` | string | **yes** | **New.** A tier name declared in `medical-tiers.toml`, checked as a cross-file rule (FR-034). |
| `always-available` | boolean | no | **New.** Default `false`. Marks the career reachable as the qualification fallback (FR-006). |
| `re-enterable` | boolean | no | **New.** Default `false`. Marks the career available again after being left (FR-015). |
| `throws.promotion` | throw | **no** | **Was required.** Absent for a career that offers no advancement (FR-035). |
| `tables.specialist` | table | yes | **Renamed** from `tables.advanced`. |
| `tables.advanced-education` | table | **yes** | **Was optional** (FR-034). Its `requires` gate stays declared in the file rather than being assumed by the engine. |
| `ladders[].role` | string | **yes** | **New.** `"entry"` or `"commissioned"` (FR-007b). Exactly one ladder carries `entry`; at most one carries `commissioned`, and a career declaring `throws.commission` MUST declare one. A commission moves the character to the commissioned ladder at the lowest rank it declares. Without this field "the officer ladder is the second one listed" is a rule held in engine code. |

`throws.commission` stays optional. A career declaring neither `commission` nor `promotion`
grants two skill rolls a term; no flag says so, and the absence of both is what says it
(FR-009). The shipped `scout.toml` and `drifter.toml` are the two careers that prove it.

Only Drifter ships with `always-available` or `re-enterable` set. A career that is always
available is still thrown for when the ordinary random selection picks it, and entered
automatically only when it is reached as the fallback (spec Assumptions, research R10).

## `draft-table` (`chargen/draft.toml`)

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "draft-table"
schema-version = 1

roll = "1d6"
careers = ["Aerospace Defense", "Marine", "Maritime Defense",
           "Navy", "Scout", "Surface Defense"]
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `roll` | string | yes | Dice notation describing a count and a side count. The `d66` literal is rejected here as it is in `task.roll`. |
| `careers` | array of string | yes | Non-empty. The row read is the throw's total, so **order is significant** (FR-005). Every entry must resolve to a career's declared `name`, checked as a cross-file rule; one that does not fails the run before any character is produced, rather than falling back. |

The number of rows and the die are not required to agree. A die that can produce a total
outside the array is a data problem reported when it is read, not at load, for the same
reason a characteristic outside the pseudo-hex range is: it depends on the throw.

## `aging-table` (`chargen/aging.toml`)

```toml
schema = "aging-table"
schema-version = 1

roll = "2d6"
modifier = "terms-served"

[[rows]]
range = "-6"
effects = [
  { class = "physical", count = 3, amount = -2 },
  { class = "mental", count = 1, amount = -1 },
]

[[rows]]
range = "0"
effects = [{ class = "physical", count = 1, amount = -1 }]

[[rows]]
range = "1+"
effects = []
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `roll` | string | yes | Dice notation. |
| `modifier` | string | yes | What is subtracted from the total. `terms-served` is the only value the engine knows; anything else is rejected, so the field names the rule rather than leaving it implicit. |
| `rows` | array of table | yes | Non-empty. |
| `rows[].range` | string | yes | `N`, `N-M`, or `N+`. May be negative. Exactly one row unbounded above. The **lowest** row is a floor: a modified result below it reads that row. |
| `rows[].effects` | array of table | yes | Possibly empty, which is how the no-effect row is written rather than being omitted. |
| `rows[].effects[].class` | string | yes | A class declared in the characteristics registry. |
| `rows[].effects[].count` | integer | yes | How many distinct characteristics of that class. At least one. |
| `rows[].effects[].amount` | integer | yes | Signed, non-zero. |

Which characteristics of the named class are chosen is the generator's decision, made at
random and recorded in the history. Where `count` exceeds the number of characteristics of
that class in force, every one of them is affected and no more.

## `mishap-table` (`chargen/mishaps.toml`)

```toml
schema = "mishap-table"
schema-version = 1

roll = "1d6"
injury-roll = "1d6"

[[mishaps]]
description = "Injured in action."
effects = [{ kind = "characteristic-class", class = "physical", count = 1, amount = "-1d6" }]

[[mishaps]]
description = "Honorably discharged from the service."
effects = []

[[mishaps]]
description = "Honorably discharged after a long legal battle."
effects = [{ kind = "debt", amount = "10000" }]

[[injuries]]
description = "Lightly injured."
effects = []
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `roll`, `injury-roll` | string | yes | Dice notation. |
| `mishaps` | array of table | yes | Non-empty. Indexed positionally by the throw's total, like the draft table. |
| `injuries` | array of table | yes | Non-empty. Reached only from a mishap effect of kind `roll-injury`. |
| `*[].description` | string | yes | Non-empty. Rendered in the fuller history line; never parsed. |
| `*[].effects` | array of table | yes | Possibly empty. |
| `*[].effects[].kind` | string | yes | One of `characteristic-class`, `debt`, `years`, `forfeit-term-benefit`, `forfeit-career-benefits`, `roll-injury`. A closed set, so a misspelling is caught rather than becoming a new effect nothing performs. |
| `*[].effects[].class` | string | for `characteristic-class` | A class in the characteristics registry. |
| `*[].effects[].count` | integer | for `characteristic-class` | At least one. |
| `*[].effects[].amount` | string | for `characteristic-class`, `debt`, `years` | Dice notation or a signed integer written as text. `"-1d6"` and `"10000"` are both valid. Written as a string uniformly so one field does not change type between rows. |

Both tables live in one file because nothing but a mishap reaches an injury, and splitting
them would let a referee replace one and leave a dangling reference in the other.

## `background-skills` (`chargen/background-skills.toml`)

```toml
schema = "background-skills"
schema-version = 1

law-level = ["Gun Combat 0", "Gun Combat 0", "Gun Combat 0", "Melee Combat 0"]
trade-code = ["Animals 0", "Zero-G 0", "Survival 0", ...]
education = ["Admin 0", "Advocate 0", "Animals 0", ...]
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `law-level` | array of notation | yes | Non-empty. Skill-table context. |
| `trade-code` | array of notation | yes | Non-empty. Skill-table context. |
| `education` | array of notation | yes | Non-empty. Skill-table context. |

The homeworld draw is uniform over the concatenation of `law-level` and `trade-code`.
Duplicates within and across those two lists are preserved and are meaningful: a skill named
by three trade codes is three times as likely as one named by a single code, which is the
nearest honest stand-in for a homeworld this feature does not generate (FR-003, research
R5).

The three lists are one file and one kind because FR-037 enumerates "the background and
homeworld skill tables" as one item and one rule draws over all three.

## `medical-tiers` (`chargen/medical-tiers.toml`)

```toml
schema = "medical-tiers"
schema-version = 1

roll = "2d6"
rank-dm = true

[[tiers]]
name = "service"
thresholds = [
  { target = 4, paid-percent = 75 },
  { target = 8, paid-percent = 100 },
]

[[tiers]]
name = "professional"
thresholds = [
  { target = 4, paid-percent = 50 },
  { target = 8, paid-percent = 75 },
  { target = 12, paid-percent = 100 },
]

[[tiers]]
name = "fringe"
thresholds = [
  { target = 8, paid-percent = 50 },
  { target = 12, paid-percent = 75 },
]
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `roll` | string | yes | Dice notation. |
| `rank-dm` | boolean | yes | Whether the character's rank is added to the total. Declared rather than assumed. |
| `tiers` | array of table | yes | Non-empty. |
| `tiers[].name` | string | yes | Non-empty, distinct across tiers. Careers reference it. |
| `tiers[].thresholds` | array of table | yes | Non-empty. Sorted internally, highest target first; the first threshold the total meets wins. |
| `tiers[].thresholds[].target` | integer | yes | Distinct within a tier. |
| `tiers[].thresholds[].paid-percent` | integer | yes | 0 through 100. What the **employer** pays; the character owes the rest. |

A total below every threshold in the tier pays nothing. That is stated here rather than left
to the engine, and it is why the `service` tier writes two thresholds where the source
prints three: a third at the same percentage would say nothing the second does not.

The tier names are this project's labels. The source material groups careers into three
tiers and names none of them; `professional` is the spec's own word (FR-032) and the other
two are chosen to match how the source groups them.

## `chargen-parameters` (`chargen/chargen-parameters.toml`)

Every rules constant the walk depends on (FR-038). None of these may appear in engine code,
and SC-013 demonstrates a behavior change from editing them.

```toml
schema = "chargen-parameters"
schema-version = 1

[characteristics]
roll = "2d6"

[background-skills]
base = 3
characteristic = "EDU"
homeworld-first = 2

[terms]
starting-age = 18
term-years = 4
mishap-term-years = 2
cap = 7
aging-begins-at-age = 34

[qualification]
penalty-per-previous-career = -2
draft-entries-allowed = 1

[basic-training]
first-career-all = true
subsequent-career-count = 1

[survival]
natural-failure = 2

[skill-rolls]
per-term = 1
per-term-without-throws = 2
on-commission = 1
on-advancement = 1

[commission]
drafted-first-term-barred = true

[continuation]
roll = "1d6"
target = 4

[mustering-out]
roll = "1d6"
maximum-cash-rolls = 3
retired-cash-dm = 1
rank-benefits = [
  { rank = 4, extra = 1 },
  { rank = 5, extra = 2 },
  { rank = 6, extra = 3 },
]
material-rank-dm = [{ rank = 5, dm = 1 }]

[pension]
minimum-terms = 5
base = 10000
per-additional-term = 2000

[medical]
crisis-roll = "1d6"
crisis-multiplier = 10000
crisis-restores-to = 1
restore-cost-per-point = 5000
```

Every key is required, and every table is a closed key set, so a misspelling is reported
rather than silently taking a default the engine holds. Notes on the ones whose meaning is
not obvious from the name:

| Key | Meaning |
|---|---|
| `background-skills.base` / `.characteristic` | The count is `base` plus that characteristic's modifier. A count below one is raised to one, which is the spec's answer to a character entitled to exactly one background skill (FR-003). |
| `background-skills.homeworld-first` | How many of the count come from the homeworld lists before the education list is reached. When the count is smaller, every skill comes from the homeworld lists. |
| `qualification.draft-entries-allowed` | How many times one character may be routed to the draft. Beyond it, a failed qualification routes to the always-available career instead. |
| `basic-training.first-career-all` | `true` grants every entry of the service table at level zero on entering the first career. `subsequent-career-count` is how many are drawn for any later career. |
| `survival.natural-failure` | An unmodified total equal to this always fails, whatever the modifiers. |
| `skill-rolls.on-commission` / `.on-advancement` | Further rolls granted by a successful throw. Shipped at one each, following the source material; setting both to zero gives FR-009's strict reading with no code edit (research R12). |
| `commission.drafted-first-term-barred` | A character who was drafted into a career may not attempt its commission in the first term. |
| `continuation.roll` / `.target` | The throw for whether the character wishes to continue serving. `1d6` against 4 is an even chance, which is the spec's chosen default (spec Assumptions). Passing it does not by itself continue the career: the re-enlistment throw still applies (FR-014). |
| `pension.minimum-terms` | Terms required **in a single career**, not across all of them (FR-018). A character with three terms in each of two careers qualifies for nothing. |
| `pension.base` / `.per-additional-term` | The amount is the base plus the increment for each term in that career above the minimum. |
| `mustering-out.rank-benefits` | Extra benefit rolls by rank reached. **Not cumulative**: the highest matching row wins (research R10). |
| `mustering-out.material-rank-dm` | A modifier on material benefit rolls by rank. Highest matching row wins. |
| `medical.crisis-roll` / `.crisis-multiplier` | A crisis costs the throw times the multiplier, and becomes a debt (FR-021). A crisis is triggered by an aging effect reducing a characteristic to the bottom of the declared pseudo-hex range. |
| `medical.crisis-restores-to` | The score a settled crisis debt lifts each covered characteristic to (FR-021). Shipped at 1, matching the source's medical care. A crisis whose debt is never settled leaves them floored. |
| `medical.restore-cost-per-point` | What restoring one point of a reduced characteristic costs, charged at the share the career's medical tier leaves to the character (FR-025). |

## `given-names` (`names/given-names.toml`)

```toml
# GPL-3.0-only project content; not Open Game Content. See LICENSE.

schema = "given-names"
schema-version = 1

source = "..."
names = ["...", "..."]
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `source` | string | yes | Non-empty. Where the entries were drawn from (FR-043e). |
| `names` | array of string | yes | Non-empty (FR-043h). Each entry non-empty. |

The key set is closed, which is what makes FR-043b's "no name table may carry a gender
field" a schema rule rather than a convention: a `gender` key is an unrecognized key and the
file is rejected.

The shipped table holds at least sixty entries (FR-043i). That is a property of the shipped
file asserted by a test, **not** a schema rule: FR-043i binds the shipped tables only and
says so, and an override's size is the referee's business.

## `surnames` (`names/surnames-*.toml`)

A repeatable kind, like `career`.

```toml
# GPL-3.0-only project content; not Open Game Content. See LICENSE.

schema = "surnames"
schema-version = 1

region = "Indigenous peoples"
source = "..."

names = [
  { name = "...", people = "..." },
  { name = "..." },
]
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `region` | string | yes | Non-empty, distinct across the tables in force, checked as a cross-file rule. |
| `source` | string | yes | Non-empty (FR-043e). |
| `names` | array of table | yes | Non-empty (FR-043h). |
| `names[].name` | string | yes | Non-empty. |
| `names[].people` | string | no | The people the name comes from. |

`people` is optional in the schema and required of the shipped indigenous-peoples table by a
test (FR-043d, SC-015b). Optional in the schema because an override adding a region carries
no such obligation; required of that shipped file because without the attribution it is a
list labeled with a category describing none of its entries.

Each shipped surname table holds at least forty entries, and the shipped tables are
deliberately of **differing** sizes so that SC-019 can fail if weighting is ever taken over
names rather than over regions.

Weighting is over the tables in force, not over the shipped seven (FR-043f). An override
replacing one region's file leaves the weighting unchanged; one adding an eighth region
gives it the same weight as each of the others.

## Composition and cross-file rules

Composition is unchanged: basename keying, whole-file replacement, dot-prefixed files passed
over when found by a walk, non-`.toml` files ignored and named.

The inherited cross-file rules still hold. This feature adds five, checked after every file
has been read.

| Rule | Requirement |
|---|---|
| Every career the draft table names resolves to a career in force | FR-005. Names the unresolvable career and fails the run before any character is produced, rather than falling back to Drifter. A fallback here would be a rule in engine code with no reason to exist once the data is complete. |
| Every career's `medical-tier` names a tier in the medical-tiers file | FR-034. |
| No two surname tables in force declare the same region | The problem names both files, in the shape the duplicate-career-name rule already uses. |
| At least one surname table is in force | FR-043f weights over the tables in force, and none in force means no surname can be drawn. |
| Every characteristic class the aging and mishap tables name is declared in the characteristics registry | FR-040a, research R12. Otherwise "reduce one physical characteristic" reaches nothing and the effect silently does not happen. |
| Every career declares exactly one `entry` ladder, and a career declaring `throws.commission` declares exactly one `commissioned` ladder | FR-007b. A commission with nowhere to move the character to is a throw whose success does nothing. |

Failure is unchanged: any problem anywhere fails the whole data set, no valid subset is
exposed, and no built-in value is substituted.
