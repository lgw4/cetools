# Research: Complete SRD Careers

**Source of truth**: <https://evolvedexperiment.github.io/cepheus-srd/>, specifically
`character-creation.html` (the careers narrative, the draft table, the medical-care table, the
mustering-out rules, and the four in-page tabs of the "Career Tables" section) and `skills.html`
(the available-skills list, the skill descriptions, and each cascade skill's specialty list).
The career tables are four tabs in one page, six careers per tab; they are not separate pages.

Everything below was read from those two pages. Where an earlier transcription in this
repository disagrees, the source wins (spec Assumptions).

## R1. The roster: twenty-four careers

The careers narrative names twenty-four and the four tabs carry six columns each. The eight the
package already ships are marked *shipped*; the sixteen to add are marked **new**.

**Column note.** `Promo.` is the **advancement (promotion) throw**, which varies by career. It is
*not* the advanced-education gate, which FR-004 fixes at `Edu 8+` for every career without
exception and which every career file carries as `[tables.advanced-education] requires`. The two
are easy to confuse because both are commonly written `Edu N+`; nothing in this table records the
advanced-education gate, because it is the same in all twenty-four.

| Career (display name) | Basename | Qual. | Surv. | Comm. | Promo. | Re-enl. | Ranks 1-6 | Material rows | Medical tier |
|---|---|---|---|---|---|---|---|---|---|
| Aerospace System Defense *shipped* | `aerospace-system-defense` | End 5+ | Dex 5+ | Edu 6+ | Edu 7+ | 5+ | yes | 7 | service |
| Agent **new** | `agent` | Soc 6+ | Int 6+ | Edu 7+ | Edu 6+ | 6+ | yes | 7 | professional |
| Athlete **new** | `athlete` | End 8+ | Dex 5+ | none | none | 6+ | no | 6 | professional |
| Barbarian **new** | `barbarian` | End 5+ | Str 6+ | none | none | 5+ | no | 6 | fringe |
| Belter **new** | `belter` | Int 4+ | Dex 7+ | none | none | 5+ | no | 6 | fringe |
| Bureaucrat **new** | `bureaucrat` | Soc 6+ | Edu 4+ | Soc 5+ | Int 8+ | 5+ | yes | 7 | professional |
| Colonist **new** | `colonist` | End 5+ | End 6+ | Int 7+ | Edu 6+ | 5+ | yes | 7 | fringe |
| Diplomat **new** | `diplomat` | Soc 6+ | Edu 5+ | Int 7+ | Soc 7+ | 5+ | yes | 7 | professional |
| Drifter *shipped* | `drifter` | Dex 5+ | End 5+ | none | none | 5+ | no | 6 | fringe |
| Entertainer **new** | `entertainer` | Soc 8+ | Int 4+ | none | none | 6+ | no | 6 | professional |
| Hunter **new** | `hunter` | End 5+ | Str 8+ | none | none | 6+ | no | 6 | professional |
| Marine *shipped* | `marine` | Int 6+ | End 6+ | Edu 6+ | Soc 7+ | 6+ | yes | 7 | service |
| Maritime System Defense *shipped* | `maritime-system-defense` | End 5+ | End 5+ | Int 6+ | Edu 7+ | 5+ | yes | 7 | service |
| Mercenary **new** | `mercenary` | Int 4+ | End 6+ | Int 7+ | Int 6+ | 5+ | yes | 7 | professional |
| Merchant *shipped* | `merchant` | Int 4+ | Int 5+ | Int 5+ | Edu 8+ | 4+ | yes | 7 | professional |
| Navy *shipped* | `navy` | Int 6+ | Int 5+ | Soc 7+ | Edu 6+ | 5+ | yes | 7 | service |
| Noble **new** | `noble` | Soc 8+ | Soc 4+ | Edu 5+ | Int 8+ | 6+ | yes | 7 | professional |
| Physician **new** | `physician` | Edu 6+ | Int 4+ | Int 5+ | Edu 8+ | 5+ | yes | 7 | professional |
| Pirate **new** | `pirate` | Dex 5+ | Dex 6+ | Str 7+ | Int 6+ | 5+ | yes | 7 | professional |
| Rogue **new** | `rogue` | Dex 5+ | Dex 4+ | Str 6+ | Int 7+ | 4+ | yes | 7 | fringe |
| Scientist **new** | `scientist` | Edu 6+ | Edu 5+ | Int 7+ | Int 6+ | 5+ | yes | 7 | professional |
| Scout *shipped* | `scout` | Int 6+ | End 7+ | none | none | 6+ | no | 6 | service |
| Surface System Defense *shipped* | `surface-system-defense` | End 5+ | Edu 5+ | End 6+ | Edu 7+ | 5+ | yes | 7 | service |
| Technician **new** | `technician` | Edu 6+ | Dex 4+ | Edu 5+ | Int 8+ | 5+ | yes | 7 | professional |

Cash tables are seven rows in every one of the twenty-four. Material tables are seven rows
except in the seven careers that offer no commission (Athlete, Barbarian, Belter, Drifter,
Entertainer, Hunter, Scout), where the source prints a dash in row 7.

The commissionless seven are named as such by the source: "Commissions and advancement are not
available in the Athlete, Barbarian, Belter, Drifter, Entertainer, Hunter and Scout careers",
and they take two skill rolls a term instead of one. The package already derives both facts from
the absence of the `commission` and `promotion` throws, so no flag is added.

## R2. The three long career names (FR-005)

- **Decision**: the display names are `Aerospace System Defense`, `Maritime System Defense`, and
  `Surface System Defense`, and the files are renamed to match.
- **Rationale**: the career-descriptions list, which is the source naming its careers rather
  than heading a table column, prints the long forms. The draft table prints them longer still,
  with a parenthetical gloss (`Aerospace System Defense (Planetary Air Force)`); the career
  tables print the short forms to fit a six-column header. FR-005 asks for the name used where
  the source is naming, which is the description list.
- **Alternatives considered**: keeping `Aerospace Defense` (the current shipped name) was
  rejected because it is a column label, not a name; adopting the draft table's parenthetical
  form was rejected because the gloss is an aside about what the career is, not part of the
  name, and it would put a parenthetical in a career name for the first time.
- **Consequence**: `draft.toml`'s `careers` array must be rewritten to the long names in the
  same commit, since `rules.py` cross-checks each draft entry against a career's declared name.

## R3. Medical tiers, always-available, and re-enterable (FR-006a)

The source states all three outside the career tables, so none of the twenty-four falls back on
a recorded default.

- **Medical care** groups all twenty-four explicitly into the three tiers whose thresholds
  `medical-tiers.toml` already carries: 75/100/100 (the six draft-eligible services), 50/75/100
  (Agent, Athlete, Bureaucrat, Diplomat, Entertainer, Hunter, Mercenary, Merchant, Noble,
  Physician, Pirate, Scientist, Technician), and 0/50/75 (Barbarian, Belter, Colonist, Drifter,
  Rogue). The tier column in R1 is that grouping.
- **Always available**: "the Drifter career is always open". Drifter alone, which is what the
  shipped `drifter.toml` already declares.
- **Re-enterable**: "Once you leave a career you cannot return to it. The Draft and the Drifter
  career are exceptions to this rule". Drifter alone, again matching what is shipped. The draft
  exception is about how a character enters, not a property of the career, and the walk already
  models it separately; no flag changes.

Because the source is silent for nothing here, the FR-006a fallback ("record the chosen default
and its reason in that career's file") is not exercised. If the re-read turns up a career the
source does not place, that career's file carries the note.

## R4. The skill vocabulary (FR-014, FR-016, FR-017)

The skill chapter defines exactly 68 skills. Eight are cascades:

| Cascade | Specialties |
|---|---|
| Gun Combat | Archery, Energy Pistol, Energy Rifle, Shotgun, Slug Pistol, Slug Rifle |
| Gunnery | Bay Weapons, Heavy Weapons, Screens, Spinal Mounts, Turret Weapons |
| Melee Combat | Natural Weapons, Bludgeoning Weapons, Piercing Weapons, Slashing Weapons |
| Sciences | Life Sciences, Physical Sciences, Social Sciences, Space Sciences |
| Animals | Farming, Riding, Survival, Veterinary Medicine |
| Vehicle | Aircraft, Mole, Tracked Vehicle, Watercraft, Wheeled Vehicle |
| Aircraft | Grav Vehicle, Rotor Aircraft, Winged Aircraft |
| Watercraft | Motorboats, Ocean Ships, Sailing Ships, Submarine |

`Vehicle` names two specialties, `Aircraft` and `Watercraft`, that are themselves cascades. That
is the nesting FR-012 exists for.

Every specialty above is also one of the 68 in its own right, so the registry can hold one entry
per chapter-defined skill and let a specialty array name other entries. See D5.

The remaining 40 chapter-defined skills carry no specialties: Admin, Advocate, Athletics, Battle
Dress, Bribery, Broker, Carousing, Comms, Computer, Demolitions, Electronics, Engineering,
Gambling, Gravitics, Jack-of-All-Trades, Leadership, Liaison, Linguistics, Mechanics, Medicine,
Navigation, Piloting, Recon, Steward, Streetwise, Survival, Tactics, Zero-G, plus the 32
specialty names listed in the table above that are not themselves cascades.

Cross-checking every name the twenty-four career tables grant against those 68 leaves exactly
five that do not match:

| As printed | Disposition | Where |
|---|---|---|
| `Jack o' Trades` | The chapter's own heading is `Jack-of-All-Trades (Jack o' Trades or JoT)`, so this is the source's sanctioned short form of a name it defines. Career data writes the canonical `Jack-of-All-Trades`; the registry file records the alias. | Adv Education and Specialist tables in nine careers |
| `Pilot` | Misspelling of `Piloting`, corrected under FR-017 with a note in each career file that carries it. Every skill *table* in the source prints `Piloting`; only the rank rows print `Pilot`. | Scout rank 0, Merchant rank 3, Pirate rank 2 |
| `Liaision` | Misspelling of `Liaison`, corrected under FR-017 with a note in the file. | Colonist rank 3 |
| `Perception` | Granted by a career table, defined nowhere in the skill chapter. Carried in the vocabulary so the grant resolves; the discrepancy is recorded in `skills.toml` (FR-016). | Bureaucrat Specialist 3 |
| `Prospecting` | Same as `Perception`. | Belter Service 5 and Specialist 4 |

`Perception` and `Prospecting` are the two skills the spec's Story 3 anticipates. The vocabulary
is therefore 70 names: the 68 the chapter defines plus those two.

Names presently in `skills.toml` that the source never uses, and which are removed: `Art`,
`Carouse` (source: `Carousing`), `Diplomat`, `Drive`, `Flyer`, `Gambler` (source: `Gambling`),
`Language` (source: `Linguistics`), `Mechanic` (source: `Mechanics`), `Persuade`, `Profession`,
`Seafarer`, `Stealth`. These are the other edition's spellings the audit found.

Career files are not the only shipped data that references this vocabulary.
`chargen/background-skills.toml` grants skill names too, and eleven of the twelve removed above
appear in it. R8 covers what that file becomes; FR-014a is why it is in scope at all.

## R5. The benefit vocabulary (FR-015)

Every distinct item the twenty-four material-benefit tables award:

`Low Passage`, `Mid Passage`, `High Passage`, `Weapon`, `Explorers' Society`, `Ship Share`,
`Courier Vessel`, `Research Vessel`. Eight items.

`Courier Vessel` is Scout's material row 6; `Research Vessel` is Scientist's row 7. Both have
their own description under "Material Benefits" alongside passages, ship shares, the Explorers'
Society, and the weapon.

Removed, because no source career awards them: `Armor`, `Personal Vehicle`, `Trade Goods`.

Characteristic adjustments (`+1 Int`, `+1 Soc`, `-1 Soc` and the like) are not benefit items and
never were; they parse as adjustments in the same table position and are checked against the
characteristics registry.

## R6. Ship shares are a rolled quantity (FR-011)

Six careers award `1D6 Ship Shares` on a material row: Belter (5), Hunter (5), Merchant (5),
Mercenary (7), Noble (7), Pirate (7). No other benefit is printed with a quantity.

The item name in the vocabulary is the singular `Ship Share`, matching the item the "Material
Benefits" prose describes ("Each ship share is worth approximately Cr2,000,000"). The source's
plural in the table cell is a plural of that item, and the notation carries the count separately.

## R7. The audit: what the shipped eight get wrong

Navy matches the source across every field checked. The other seven differ as follows.

- **Scout** (`scout.toml`): qualification is `Int 5+`, source `Int 6+`; re-enlistment is `3+`,
  source `6+`; rank 0 grants `Survival 1` and a title `Scout`, source grants `Pilot-1` and
  prints no title; the cash table is `[20000, 20000, 30000, 30000, 50000, 50000, 50000]`, source
  `[1000, 5000, 10000, 10000, 20000, 50000, 50000]`; the material table's seventh row is a
  padded repeat and the source prints a dash there; service skills differ from the source's
  `Comms, Electronics, Gun Combat, Gunnery, Recon, Piloting`; the material rows differ
  throughout, and the source's row 5 and row 6 are `Explorers' Society` and `Courier Vessel`.
- **Drifter** (`drifter.toml`): qualification is `End 3+`, source `Dex 5+`; the
  advanced-education gate is `EDU 6+`, source `Edu 8+` for every career without exception
  (FR-004); the cash table is `[1000, 1000, 2000, 2000, 5000, 5000, 5000]`, source
  `[0, 1000, 2000, 5000, 5000, 10000, 10000]`; the material table's seventh row is a padded
  repeat where the source prints a dash; rank 0 carries the title `Drifter`, and the source
  prints nothing at all in every rank row; benefit items include `Trade Goods` and
  `Personal Vehicle`, which the source never awards; skill tables use `Carouse`, `Gambler` and
  `Stealth`, names the source does not define.
- **Aerospace Defense, Marine, Maritime Defense, Merchant, Surface Defense**: each ships a
  seven-row material table whose seventh row is a comment-acknowledged repeat of the sixth, and
  each draws on the mixed vocabulary of R4. These are reconciled field by field alongside the
  other nineteen rather than singled out; the re-read (FR-023) is what establishes their state,
  not this summary.

The uniform `Edu 8+` advanced-education gate is stated once, for every career: "You may only
roll on the Advanced Education table if your character has Education 8+."

## R8. The background-skills table (FR-014a)

`background-skills.toml` is not career content, and this feature would not have touched it if
rebuilding the skill vocabulary had not broken it. Eleven of the names it grants — `Art`,
`Carouse`, `Diplomat`, `Drive`, `Flyer`, `Gambler`, `Language`, `Mechanic`, `Profession`,
`Seafarer`, `Stealth` — are names R4 removes, so after the rebuild the file stops resolving and
`tests/unit/test_rules_agreement.py::test_every_background_skill_the_packaged_table_grants_resolves`
fails. Reading the source to retarget it showed the file is not merely misspelled: two of its
three lists are a different table altogether.

The source's three lists, read from `character-creation.html`'s Background Skills section:

| List | Source rows, in printed order |
|---|---|
| law-level (4) | Gun Combat, Gun Combat, Gun Combat, Melee Combat |
| trade-code (14) | Animals, Zero-G, Survival, Watercraft, Animals, Computer, Streetwise, Zero-G, Broker, Survival, Animals, Carousing, Watercraft, Zero-G |
| education (15) | Admin, Advocate, Animals, Carousing, Comms, Computer, Electronics, Engineering, Life Sciences, Linguistics, Mechanics, Medicine, Physical Sciences, Social Sciences, Space Sciences |

Every one of those names is among R4's seventy, so the retarget needs no vocabulary addition.

Three things to note:

- **law-level already matches**, including its `Gun Combat` triple.
- **trade-code does not match at all.** The shipped list is fourteen alphabetized names with no
  repeats; the source prints fourteen rows keyed to trade codes, with `Animals` three times,
  `Zero-G` three times, and `Survival` and `Watercraft` twice each. The shipped file's own header
  comment claims "duplicates are preserved and meaningful", which is the rule — and the shipped
  data breaks it, flattening a weighted draw into a uniform one over the wrong names.
- **education does not match either**, though it is the same length by coincidence.

The count rule is unchanged and already correct: "3 + your Education DM", which
`chargen-parameters.toml` carries as `base = 3`, `characteristic = "EDU"`.

**Consequence**: this changes which skills a character starts with, so it contributes to the
seed-output break alongside the enlarged pool (FR-029). It is transcribed and verified on the
same terms as a career (FR-014a, FR-023a), not patched name by name.

**A second consequence, and a visible one.** The education list grants `Life Sciences`,
`Physical Sciences`, `Social Sciences`, and `Space Sciences` bare, and each of those four is also
a specialty of the `Sciences` cascade. That is the `Animals`/`Survival` situation of D6 — but
background skills go to *every* character, where D6's case needed a career grant to collide with a
top-level grant. So a sheet reading

```text
Life Sciences-0, Sciences (Life Sciences)-1
```

stops being an override curiosity and becomes routine output.

No rule changes: D6 and FR-016a already settle it, and the two are distinct entries because the
skill book keys on `(name, specialty)`. What changes is that the outcome is now common enough to
need pinning in a test rather than reasoned about (T035) and naming in the changelog (T090), so it
is not read as a duplicate-skill bug by the first person to see one. `Watercraft`, `Animals`,
`Gun Combat`, and `Melee Combat` are likewise cascades granted bare by these lists, and resolve
through to a terminal specialty exactly as any other bare cascade grant does (FR-012).

## Decisions

### D1. Career schema rises to version 4

Three changes, all of which the current shape cannot express or wrongly requires:

1. `ranks[].title` becomes optional. A rank whose source row prints no title omits the key. An
   explicit `title = ""` stays rejected, because absence is expressed by absence (FR-013) and an
   empty string in the file is an author saying something rather than saying nothing.
2. `mustering-out.benefits` entries admit a dice-quantity form (D3).
3. `throws.re-enlistment` no longer admits `characteristic`. Every one of the twenty-four
   re-enlistment throws is a bare target (`5+`, `6+`, `4+`); no source career modifies it by a
   characteristic, and the walk already ignores the field for that throw. Leaving it admissible
   is a field that means nothing and would let an override silently declare a modifier the
   engine drops.

**Alternatives considered**: leaving the version at 3 and treating an omitted title as a
tolerated absence was rejected because a v3 reader is entitled to require the key, and an
override written against v3 must be told its assumption changed. Bundling the three changes into
one bump rather than three is the right granularity: they land together and no data set exists
between them.

### D2. `Rank.title` stays a `str`, defaulting to `""`

The parsed type keeps `title: str` and defaults to the empty string when the key is absent,
rather than becoming `str | None`.

**Rationale**: the empty string is already the "no title" marker everywhere downstream.
`_current_title` returns `""` for a rank it cannot find, `run()` tests `if title:` before
carrying a title forward, the Universal Character Format already omits the title and its
separator when it is empty (`tests/golden/npc_untitled.txt` pins this), and the JSON contract
already types `title` as a present string. FR-009 says explicitly to keep the empty string. A
`None` would ripple into all four with no gain.

**Alternatives considered**: `str | None` was rejected on the above; a separate `titled: bool`
flag was rejected as a second representation of one fact.

### D3. The dice-quantity benefit form anchors on the leading token

Grammar addition, admissible only in `EntryContext.BENEFIT_TABLE`:

```text
quantified := dice WS name
```

`"1d6 Ship Share"` parses to a new entry type carrying the dice notation and the item name. The
name is resolved against the benefits registry exactly as a bare item is; the dice notation is
checked by the same `_check_dice` every other dice field uses, which rejects `d66` for the same
reason it is rejected elsewhere.

**Rationale**: the trailing whitespace-delimited token is already spoken for by the three
suffixed forms (check, adjustment, grant), and `parse_entry` decides which form an entry is by
looking there. A trailing count would be ambiguous with the grant form. The source prints the
quantity in front (`1D6 Ship Shares`), so a leading anchor is both unambiguous and faithful.

**Alternatives considered**: a table-valued benefit entry (`{ item = "Ship Share", count =
"1d6" }`) was rejected because every other cell in the career schema is a notation string and
one table-valued cell would fork the shape; hard-coding "Ship Share is rolled" in the generator
was rejected outright by Constitution V and FR-011.

**Consequence for the sheet** (FR-011, spec clarification): the walk rolls the quantity from the
seeded roller and appends the item name that many times, so the existing repeat-collapsing
renderer prints `Ship Share (x3)` and the machine-readable `benefits` list holds three identical
plain strings. No quantity field enters the JSON contract.

### D4. The skills registry rises to version 2, with the file shape unchanged

`skills.toml` keeps `"<name>" = [ "<specialty>", ... ]`. What changes is the meaning: a
specialty that is itself a key with a non-empty array is a nested cascade, and resolution
continues through it.

**Rationale**: the source's nesting is exactly "a specialty that is another cascade skill", and
the registry already has an entry per skill. Representing the nesting by reference costs no new
syntax, keeps every name declared once, and makes `Aircraft` both a Vehicle specialty and a
grantable skill in its own right, which is what the career tables need (Aerospace System Defense
grants `Aircraft` directly; Maritime System Defense grants `Watercraft`).

The version bump is required even though the bytes' shape is unchanged, because a version-1
reader stops at `Aircraft` and records a skill for which no rule defines a level, which is
precisely what FR-012 forbids.

**Alternatives considered**: writing nesting into the name (`"Vehicle (Aircraft)" = [...]`) is
already rejected by `parse_skills`, which refuses a key containing parentheses, and for good
reason: nothing can reference such a key. A separate `[cascades]` table was rejected as a second
place to declare the same relationship.

### D5. Resolution records the innermost cascade and its terminal specialty

Resolving a bare `Vehicle` grant draws a specialty, and if that specialty is itself a cascade,
draws again from its specialties, until it reaches a name with none. The recorded skill is the
last cascade and the terminal choice: `Vehicle` can resolve to `Aircraft (Winged Aircraft)`, and
`Melee Combat` still resolves to `Melee Combat (Slashing Weapons)` as it does today.

**Rationale**: `SkillReference` holds one name and one optional specialty. Recording
`Vehicle (Aircraft)` leaves a name no rule gives a level, which FR-012 forbids. Recording the
bare terminal (`Winged Aircraft`) loses the cascade the level belongs under, and the source
speaks of levels "under Melee Combat". Recording the innermost pair keeps the existing display
convention and the existing type unchanged.

**Cycle safety**: a specialty chain that returns to a name already visited is a data error,
reported at validation with the file, the location, and the cycle, not discovered as a hang
during generation.

**Alternatives considered**: widening `SkillReference` to a path of names was rejected as a
change rippling through the skill book, the renderer, the JSON contract, and the goldens, for a
nesting the source only ever takes two levels deep.

### D6. `Animals (Survival)` and `Survival` stay distinct

`Survival` is both a top-level skill and one of `Animals`'s four specialties, and several
careers grant it bare. A character can therefore end with both `Survival-1` and
`Animals (Survival)-0`.

**Decision**: transcribe it. The skill book keys on `(name, specialty)` and the two are
different keys.

**Rationale**: this is what the source says, and the rule this feature establishes is that the
data says what the source says. Collapsing them would require engine code holding the knowledge
that one specialty is an alias of one top-level skill, which is table content in code
(Constitution V) and an adaptation rather than a transcription (FR-013).

**Alternatives considered**: dropping `Survival` from `Animals`'s specialty list was rejected as
editing the source; aliasing at resolution time was rejected on the above.

### D7. The mustering-out coverage check is a cross-file rule in `rules.py`

For each career in force:

- highest reachable rank = the maximum `rank` across all of that career's ladders;
- the largest total a table roll can reach = the maximum face total of
  `chargen.mustering-out.roll` plus the applicable row modifier;
- the cash table's modifier is `retired-cash-dm`, which applies in every career because the
  retirement bonus is not rank-conditioned;
- the material table's modifier is the highest `material-rank-dm` row at or below the highest
  reachable rank, which is zero in a career whose ladders stop at rank 0.

A table shorter than its bound is a problem naming the file, `mustering-out.cash` or
`mustering-out.benefits`, the row count found, and the row count required.

**Rationale**: the check needs both a career file and `chargen-parameters.toml`, so it cannot
live in `careers.py`, which parses one file against the registries. `rules.py` already hosts
every rule of that shape (the medical-tier name check, the commission-without-ladder check, the
draft-name check).

Under the packaged data this yields 7 for every cash table, 7 for the seventeen careers whose
ladders reach rank 5, and 6 for the seven that stop at rank 0, which is exactly the row counts
the source prints. It replaces the fixed `len(...) == 7` assertion in
`tests/integration/test_data_driven.py`, which the seven short tables would otherwise fail.

**Alternatives considered**: keeping the fixed length and padding the seven short tables is
forbidden by FR-010; leaving the rule in documentation is forbidden by FR-021.

### D8. Renaming three career files is structural, and is done now

Override composition keys on basename (`rules._compose`), and `RulesData.careers` keys on the
basename stem, so `aerospace-defense.toml` to `aerospace-system-defense.toml` changes a public
composition key and a library-visible mapping key while changing no CLI output. It is done in
its own commit before any content change, per Tidy First, and it is free only until the package
is published, which this release precedes.

### D9. Rank titles are transcribed as printed, abbreviations included

Physician's ranks 4 and 6 print `Attending Phys.` and `Hospital Admin.`; they are carried
verbatim. `Assistant Directory` (Agent rank 5) is the one misspelled rank title FR-017 names and
is corrected to `Assistant Director`, with the correction noted in `agent.toml`.

**Rationale**: FR-005's long-name reasoning is about career names, where the source demonstrably
uses a fuller form elsewhere. For these two rank titles the source prints an abbreviation and
prints it nowhere else, so expanding them would be invention. A misspelling is different in kind
from an abbreviation, and FR-017 already draws that line.

### D10. Noble ships with ordinary rank titles, and says so in its file (FR-031)

`noble.toml` carries `Knight`, `Baron`, `Marquis`, `Count`, `Duke`, `Archduke` as rank titles on
its commissioned ladder, and a header comment recording that the source's separate
Social-Standing nobility table is unimplemented and that whatever implements it must reconcile
with these, not duplicate them.

## Open questions

None. Every NEEDS CLARIFICATION the Technical Context could have carried was resolved by reading
the two source pages; the five questions the spec's clarification session raised are already
answered there and are honored in D2, D3, D7, and R3.
