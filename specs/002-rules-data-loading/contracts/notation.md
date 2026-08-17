# Contract: The Compact Table Notation

**Feature**: `002-rules-data-loading`

The notation is how a table entry that mixes kinds of thing in one cell is written
(FR-004). It applies to exactly the fields `contracts/data-files.md` marks as
notation-bearing and to no others: cash amounts and throw targets are plain typed
values and never reach the parser (FR-004a).

## Grammar

```text
entry          := check | adjustment | grant | bare
check          := characteristic WS uint "+"
adjustment     := characteristic WS sign uint
grant          := name WS uint
bare           := name

name           := text [ WS "(" text ")" ]
characteristic := text
sign           := "+" | "-"
uint           := one or more ASCII digits
WS             := one or more spaces
```

`text` is any run of characters other than parentheses, with leading and trailing
spaces trimmed. Skill names contain spaces, apostrophes, slashes and hyphens
(`Ship's Boat`, `Vacc Suit`, `Air/Raft`, `Jack-of-all-Trades`), so a name is never
tokenized on whitespace.

A specialty belongs to a skill or a benefit item, and a characteristic never carries
one, which is why `check` and `adjustment` take a `characteristic` rather than a
`name`. `INT (Foo) 4+` and `STR (Foo) +1` are malformed (FR-009) rather than gates on
`INT` and adjustments to `STR` with the parenthesized text discarded: dropping it
would leave content an author wrote with no effect and no diagnostic, and would evade
the exact registry match FR-013 requires, since the name as written is `INT (Foo)` and
the characteristics registry holds only `INT`.

## Parsing

Matched by anchoring on the tail of the entry, in this fixed order:

| Order | Tail | Form | Yields |
|---|---|---|---|
| 1 | `<space><digits>+` | check | `CharacteristicCheck(characteristic, target)` |
| 2 | `<space><sign><digits>` | adjustment | `CharacteristicAdjustment(characteristic, amount)` |
| 3 | `<space><digits>` | grant | `SkillGrant(SkillReference(...), level)` |
| 4 | nothing matched | bare | `SkillReference(...)` or `BenefitItem(name)`, by context |

What is left of the entry after the tail is removed is the name, which is then split
into a base name and an optional parenthesized specialty (FR-006).

Examples:

| Written | Form | Parsed |
|---|---|---|
| `INT 4+` | check | characteristic `INT`, target `4` |
| `STR +1` | adjustment | characteristic `STR`, amount `+1` |
| `SOC -1` | adjustment | characteristic `SOC`, amount `-1` |
| `Pilot 2` | grant | skill `Pilot`, no specialty, level `2` |
| `Blade (Cutlass) 1` | grant | skill `Blade`, specialty `Cutlass`, level `1` |
| `Vacc Suit` | bare | skill `Vacc Suit`, no specialty |
| `Gun Combat (Slug Rifle)` | bare | skill `Gun Combat`, specialty `Slug Rifle` |
| `Low Passage` | bare | benefit item `Low Passage` (benefit context only) |

## Contexts

The field an entry sits in fixes which forms are admissible and which registry
validates each name (FR-005, FR-009a). The three subsets below are now stated in the
spec; this table is their expansion to the fields that bear them.

| Context | Fields | Admissible forms | Registry |
|---|---|---|---|
| Skill table | `tables.*.entries`, `ladders[].ranks[].bonus` | adjustment, grant, bare | characteristics for adjustment; skills for grant and bare |
| Benefit table | `mustering-out.benefits` | adjustment, bare | characteristics for adjustment; benefit items for bare |
| Gate | `tables.*.requires` | check | characteristics |

A well-formed entry in the wrong context is a problem reporting the entry as written
and the forms acceptable in that position (FR-009, FR-009a). `INT 4+` in a service table
and `Pilot 2` in a benefits table are both rejected on this rule.

Note that a benefit table validates against two registries: bare names against benefit
items, and adjustments against characteristics. FR-005 permits this explicitly, scoping
its "and no other" to bare names, because an adjustment carries its own meaning rather
than taking it from position.

Every registry lookup is exact and case sensitive (FR-013), so `int 4+` fails on the
characteristic rather than being folded to `INT`.

## Specialties

A `SkillReference` resolves against the skills registry with four distinguishable
outcomes (FR-007, FR-008):

| Reference | Registry says | Outcome |
|---|---|---|
| `Vac Suit` | no such skill | unrecognized skill name |
| `Admin (Legal)` | `Admin` has no specialties | specialty given for a skill that has none |
| `Blade (Chainsaw)` | `Blade` has specialties, not that one | unrecognized specialty for that skill |
| `Blade (Cutlass)` | listed | valid, fully specified |
| `Blade` | has specialties, none given | valid, a choice is owed |

The last two are both valid and stay distinguishable in the loaded data, so a later
consumer can tell that a choice is owed without engine code knowing which skills owe
one (FR-008).

## Malformed entries

Each is a problem carrying the entry as written, its location, and what was expected:

| Written | Problem |
|---|---|
| `""` | empty entry |
| `"   "` | empty entry |
| `Pilot -` | trailing sign with no number |
| `Pilot (` | unbalanced parenthesis |
| `Pilot ()` | empty specialty |
| `Pilot (A) (B)` | more than one specialty group |
| `INT +4+` | not one of the four forms |
| `INT (Foo) 4+` | specialty on a characteristic check |
| `STR (Foo) +1` | specialty on a characteristic adjustment |
| `2` | empty name |
| `Pilot -1` | negative level, in a context where the adjustment form is admissible but `Pilot` is not a characteristic; reported as an unrecognized characteristic |

Non-string content in a notation-bearing field (an integer where an entry was
expected) is a type problem reported against the field, not routed to the parser.

## Trap

A name whose last space-delimited token is a bare integer parses as a grant. No name
in any shipped registry ends that way, and the registry check catches the truncated
remainder, but the diagnostic points at the skill name rather than at the number.
Recorded so a future registry addition of such a name is a considered decision.
