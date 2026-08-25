# Data files: the 004 delta

A delta on [003-npc-generator/contracts/data-files.md](../../003-npc-generator/contracts/data-files.md).
Only the files whose contract changes appear here. Discovery, composition, the header keys, the
kind-and-version gate, the problem shape, and every unmentioned file are unchanged.

## Directory layout

```text
src/cetools/data/
├── tasks.toml
├── registries/
│   ├── characteristics.toml
│   ├── skills.toml                       # skills, v2   <- version bump
│   └── benefits.toml                     # benefits, v1 <- contents rebuilt
├── chargen/
│   ├── draft.toml                        # contents: the three long career names
│   ├── aging.toml
│   ├── mishaps.toml
│   ├── background-skills.toml
│   ├── medical-tiers.toml
│   └── chargen-parameters.toml
├── names/
│   └── ...
└── careers/                              # career, v4, twenty-four files
    ├── aerospace-system-defense.toml     # renamed from aerospace-defense.toml
    ├── agent.toml                        # new
    ├── athlete.toml                      # new
    ├── barbarian.toml                    # new
    ├── belter.toml                       # new
    ├── bureaucrat.toml                   # new
    ├── colonist.toml                     # new
    ├── diplomat.toml                     # new
    ├── drifter.toml
    ├── entertainer.toml                  # new
    ├── hunter.toml                       # new
    ├── marine.toml
    ├── maritime-system-defense.toml      # renamed from maritime-defense.toml
    ├── mercenary.toml                    # new
    ├── merchant.toml
    ├── navy.toml
    ├── noble.toml                        # new
    ├── physician.toml                    # new
    ├── pirate.toml                       # new
    ├── rogue.toml                        # new
    ├── scientist.toml                    # new
    ├── scout.toml
    ├── surface-system-defense.toml       # renamed from surface-defense.toml
    └── technician.toml                   # new
```

Composed file count rises from 26 to 42. The three renames change composition keys: an override
replacing `aerospace-defense.toml` no longer replaces anything and is composed as an addition
instead. That is a breaking change, called out in the changelog; this release precedes
publication, so no published consumer is affected.

Every file under `careers/` and `registries/` is Open Game Content, carries the OGC header
comment, and contains neither of the two Product Identity strings.

## `skills` v2 (`registries/skills.toml`)

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "skills"
schema-version = 2

[skills]
"Vehicle" = ["Aircraft", "Mole", "Tracked Vehicle", "Watercraft", "Wheeled Vehicle"]
"Aircraft" = ["Grav Vehicle", "Rotor Aircraft", "Winged Aircraft"]
"Watercraft" = ["Motorboats", "Ocean Ships", "Sailing Ships", "Submarine"]
"Winged Aircraft" = []
# ...
```

| Field | Type | Required | Rule |
|---|---|---|---|
| `skills.<name>` | array of string | yes | The skill's permitted specialties; empty for a skill with none. `<name>` contains no parenthesis: a specialty is declared in the array, never spelled into the name (unchanged from v1). |

**What v2 changes.** A specialty is permitted to name another entry in the same table, and when
that entry declares specialties of its own it is a nested cascade: resolving the outer skill
continues into it, and continues again, until it reaches an entry with no specialties. A
version-1 reader stops at the first choice and records a name for which no rule defines a level,
which is why the shape being unchanged does not make the version bump optional.

**New validation rule.** The specialty graph must be acyclic. A chain that revisits a name is
reported at `skills.<name>` naming the cycle. Without it, generation-time resolution would not
terminate.

**Unchanged.** A specialty need not be an entry in the table; one that is not is terminal, which
is how v1 behaved for every specialty. Every specialty in the packaged registry *is* an entry,
because the source's skill chapter defines each of them as a skill in its own right.

**Contents.** Exactly the seventy names of research R4: the sixty-eight the source's skill
chapter defines, plus `Perception` and `Prospecting`, which career tables grant and the chapter
never defines. Those two carry a comment in the file recording the discrepancy. The file also
records that `Jack o' Trades` is the source's own short form of `Jack-of-All-Trades`, which
career data writes in the canonical spelling.

## `benefits` v1 (`registries/benefits.toml`)

Schema unchanged. Contents become exactly the eight items the twenty-four careers' material
tables award: `Low Passage`, `Mid Passage`, `High Passage`, `Weapon`, `Explorers' Society`,
`Ship Share`, `Courier Vessel`, `Research Vessel`. `Armor`, `Personal Vehicle`, and
`Trade Goods` are removed; no source career awards them.

## `career` v4 (`careers/*.toml`)

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "career"
schema-version = 4

name = "Scout"
medical-tier = "service"

[throws.qualification]
characteristic = "INT"
target = 6
dice = "2d6"

[throws.survival]
characteristic = "END"
target = 7
dice = "2d6"

[throws.re-enlistment]
target = 6
dice = "2d6"

# ... tables ...

[[ladders]]
name = "scout"
role = "entry"
ranks = [
  # The source prints a grant here and no title.
  { rank = 0, bonus = "Piloting 1" },
]

[mustering-out]
cash = [1000, 5000, 10000, 10000, 20000, 50000, 50000]
# Six rows: the source prints a dash in row 7, and Scout's ladder stops at
# rank 0, so no roll can reach a seventh row.
benefits = ["Low Passage", "EDU +1", "Weapon", "Mid Passage", "Explorers' Society", "Courier Vessel"]
```

Only the three changes below differ from v3. Every other field, and every v3 rule not restated
here, is unchanged.

| Field | Type | Required | Change from v3 |
|---|---|---|---|
| `throws.re-enlistment.characteristic` | string | n/a | **Removed.** The position now admits exactly `target` and `dice`; a `characteristic` there is an unrecognized key. No source career modifies re-enlistment by a characteristic, and the walk never read the field for this throw, so admitting it let an override declare a modifier that was silently dropped. |
| `ladders[].ranks[].title` | string | **no** | **Was required.** Omit the key for a rank whose source row prints no title. When present it must be a non-empty string; an explicit `title = ""` is rejected, because absence is written by omitting the key rather than by writing an empty value. A rank with neither `title` nor `bonus` is valid, and is what Drifter's rank 0 is. |
| `mustering-out.benefits[]` | notation | yes | **Widened.** In addition to a bare benefit item and a characteristic adjustment, the position now admits a quantified benefit: dice notation, a space, then the item name. See [notation.md](./notation.md). |
| `mustering-out.cash`, `mustering-out.benefits` | array | yes | **Length is no longer fixed.** Each ends at the last row the source prints and is padded to no length. Both are bounded below by the coverage rule, and by nothing above. |

### Cross-file rule: mustering-out coverage

New. Stated over the careers in force, so an override career file is subject to it.

For each career, with `roll` the parsed `chargen.mustering-out.roll` and `highest_rank` the
maximum rank across all of that career's ladders:

- `len(mustering-out.cash)` must be at least
  `roll.count * roll.sides + roll.modifier + chargen.mustering-out.retired-cash-dm`.
- `len(mustering-out.benefits)` must be at least
  `roll.count * roll.sides + roll.modifier` plus the highest `chargen.mustering-out.material-rank-dm`
  row at or below `highest_rank`, or plus zero when no row applies.

A shortfall is a problem naming the file, `mustering-out.cash` or `mustering-out.benefits`, the
row count found, and the row count required. The retirement modifier is unconditional because
the pension depends on the character's total terms rather than on the career's ranks; the
material modifier is rank-conditioned, so a career whose ladders stop at rank 0 is bounded by
the roll alone.

This turns what was a documented convention and a fixed-length test assertion into a rule the
`validate` command enforces (FR-021), which is what makes a short table safe rather than a
runtime failure some seed finds mid-batch.

## `draft-table` v1 (`chargen/draft.toml`)

Schema unchanged. The `careers` array becomes the three long names alongside the three
unchanged ones, in the source's printed row order:

```toml
careers = ["Aerospace System Defense", "Marine", "Maritime System Defense",
           "Navy", "Scout", "Surface System Defense"]
```

The existing cross-file rule already requires every entry to resolve to a career's declared
`name`, so this file and the three renamed career files change in the same commit.
