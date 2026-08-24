# Phase 0 Research: NPC Generator

**Feature**: `003-npc-generator` | **Date**: 2026-08-21

Every Technical Context unknown is resolved below. Findings marked **verified** were
confirmed against the source material or against code run on this machine. Findings marked
**decision** are design choices with no empirical component. Findings marked **resolution**
settle a place where the source material contradicts itself or the specification, and each
one says which side won and why.

The source material was read at `https://evolvedexperiment.github.io/cepheus-srd/`,
chapters `character-creation`, `introduction`, `skills`, and `worlds`. The Product Identity
strings are deliberately not reproduced anywhere in this document's data examples.

## R1: How the walk is driven, and where its randomness comes from

**Decision**: one `Roller` drives the walk. `generate_character(roller, rules, *,
name=None)` consumes it from the first characteristic throw to the last mustering-out roll,
and the character records `roller.seed`. Nothing else in the walk reads a clock, an
environment variable, a locale, or the traversal order of an unordered collection
(FR-056).

Every point where the source material hands a choice to a player becomes a draw:
which career is selected, which skill table a skill roll reads, which specialty a cascade
grant takes, which characteristic a "one physical characteristic" reduction lands on,
whether a benefit roll is taken as cash or as material, and whether the character wishes to
continue serving. Each of those is recorded as its own history step, so a surprising sheet
names the draw that produced it (FR-030).

**Rationale**: the constitution's Principle IV and FR-056 together leave no other shape.
Threading one roller rather than several also means the walk has a single, inspectable
consumption order, which is what makes the same seed reproduce the same person after any
refactor that does not change the order of draws.

**Consequence to guard**: the order of draws is part of the contract in the same way the
golden files are. Reordering two independent draws changes every character. That is not a
defect to be designed away, it is what reproducibility costs, and the golden files are what
detects it.

## R2: Batch seeds, and why position zero is the master itself

**Decision**: character *i* of a batch runs on

```python
def character_seed(master: int, index: int) -> int:
    return master if index == 0 else derive_seed(master, index)
```

where `derive_seed` folds the master and the index through the blake2b digest `seeds.py`
already uses for text seeds and negative seeds. `generate_batch(seed, rules, *, count=1,
name=None)` builds one `Roller` per position from that value.

**Rationale**: three requirements have to hold at once, and only this shape holds all three.

| Requirement | What it needs |
|---|---|
| FR-057, the prefix property | Position *i* depends on `(master, i)` and nothing else, so a batch of twelve begins with the batch of three. |
| FR-048a, a batch of one | The single character of a seed and position 0 of a batch of that seed are the same person, byte for byte. |
| FR-050a, the per-character seed | The derived seed a character carries, quoted back to `--seed`, regenerates that one person. |

A single roller drawn sequentially satisfies the first and fails the third: character 5's
walk continues the stream character 4 left, so no standalone seed reproduces it. Deriving
every position including zero satisfies the first and the third but fails the second,
because `--seed X` would then produce `derive_seed(X, 0)` and the reported seed would not
round-trip. Making position 0 the master itself is what closes the triangle: the reported
seed for position *i* is the walk seed, feeding it back as a master runs it at position 0,
and position 0 is the identity.

**Alternatives considered**: drawing each position's seed from a master roller, which is
literally "sequential from one roller" and yields standalone seeds, rejected because it
still needs the position-zero identity to make the round trip work, and it additionally
requires `Roller` to grow a bit-drawing method that nothing else in the package wants
(Principle VI). Reporting `(master, index)` as the reproduction key instead of a seed,
rejected because FR-050a asks for a seed that reproduces one person, and a pair is not
something a referee can type after `--seed`.

**Verified**: `derive_seed` returns a value in the same space `resolve_seed` accepts, so a
reported decimal string round-trips through `resolve_seed` unchanged. The existing
`rng_seed` fold is reused rather than a second digest being introduced.

## R3: The name stream is separate, and that is the whole of FR-047b

**Decision**: the rolled name is drawn from `Roller(derive_seed(character_seed, "name"))`,
a roller the walk never touches. A caller-supplied name skips the draw. The walk's roller is
identical in both cases.

**Rationale**: FR-047b requires that naming a character not change who they turned out to
be, and FR-056a requires the name to be seeded like everything else. The natural
implementation, rolling the name at the top of the walk from the walk's own roller, shifts
every subsequent draw when the name is supplied, and would silently make `--name` produce a
different person. Nothing else in the spec would have caught it, which is why the
requirements checklist recorded it as a trap.

A derived sub-stream costs one extra `Roller` per character and makes the property hold by
construction rather than by an ordering discipline someone has to remember.

**Consequence**: the test that proves it is a field-by-field comparison of the same seed
generated with and without a supplied name, differing in `name`, `given_name`, `surname`,
and `surname_region` and in nothing else (SC-018). It is written before the walk exists.

## R4: The Universal Character Format

**Verified** against the source material's own template and its single worked example.

The format is three fixed lines plus up to two conditional ones, tab separated:

```text
[name]<TAB>[UPP]<TAB>Age [age]
[careers]<TAB>Cr[funds]
[skills]
[species traits, if not human]
[significant property]
```

The one example the source material prints uses a single tab in both positions on line 1,
while its template writes two before `Age`. That is an inconsistency in the source, and it
is resolved here under FR-046's "exactly one tab between fields".

**Resolutions this feature makes, each in FR-046's list of places the format is silent or
contradicts itself:**

| Question | Resolution | Why |
|---|---|---|
| Tab count between UPP and `Age` | Exactly one | FR-046 fixes one tab between fields; the source's own example already uses one. |
| Skill order | Alphabetical, `(casefold, codepoint)` | The template says alphabetical; the example is not. FR-046 takes the template. See R8 for the key. |
| Cascade specialization | `Gun Combat (Slug Rifle)-1` | FR-046 requires it written qualified by its parent so a reader can find it in the registry. The source's example prints the bare specialty; the spec overrides. |
| Multiple careers | `Navy (4 terms), Drifter (1 term)` | FR-046: comma separated, in the order entered. Singular `term` at one, plural above. |
| Rank title placement | Title, one space, then the name: `Captain Bruce Ayala` | The source says "with rank and/or noble title, if appropriate" and gives no example and no separator. A title precedes a name in every form the source itself writes elsewhere. |
| Noble titles | Never rendered | FR-048. The source's own noble titles carry a gendered second form, and gender is out of scope. |
| Line 4, species traits | Never emitted | Every generated character is human (spec Out of Scope), so this is the line that is always inapplicable. |
| Line 5, significant property | The benefit items, `, ` joined, repeats collapsed to `Name (x2)`, sorted by the same key skills use | The source's example collapses repeats exactly this way. Sorting rather than keeping walk order, so the line is stable and locale-independent for the same reason the skill line is. Omitted entirely when the character holds no benefit items, which is FR-044's omissible line. |
| Funds | `Cr70,000`: prefix, no space, thousands separators | FR-045, and the source's example. |

**Not in the format, and therefore not rendered**: there is no homeworld line and no trade
code line. The source's trade code table feeds background skill selection and is never
printed. The spec's Out of Scope mentions "the trade-code row" as a row of that selection
table, not as a line of the sheet.

## R5: The universal chargen tables, and what each one's file holds

**Verified** shapes, taken from the source material.

| Kind | File | Shape |
|---|---|---|
| `draft-table` | `chargen/draft.toml` | A die and six ordered rows, each naming a career. The row order is significant because the die that reads it is positional (FR-005). |
| `aging-table` | `chargen/aging.toml` | A die (`2d6`), a modifier taken from the total terms served, and eight banded rows from `-6` to `1+`. The bottom band is a floor: a modified result below it reads that row. |
| `mishap-table` | `chargen/mishaps.toml` | A die (`1d6`) and six rows, each carrying a description and a list of structured effects. It also holds the injury table two of its rows defer to, because an injury result is a mishap consequence and nothing else reaches it. |
| `background-skills` | `chargen/background-skills.toml` | Three arrays: the law-level list (4 entries), the trade-code list (14), and the education list (15). One kind rather than two, because the spec's FR-037 enumerates "the background and homeworld skill tables" as a single item and one rule draws over all three. |
| `medical-tiers` | `chargen/medical-tiers.toml` | A die (`2d6`), a modifier taken from rank, and three named tiers, each with three thresholds and the share the employer pays at each. A modified result below the lowest threshold pays nothing, which the source does not print and this file states. |
| `chargen-parameters` | `chargen/chargen-parameters.toml` | Every scalar FR-038 enumerates, plus the ones the walk needs that FR-038's "at minimum" leaves open. Listed in full in `contracts/data-files.md`. |

**Decision on tier names**: the source groups careers into three medical tiers and names
none of them. They have to be named to be referenced from a career file. The names used are
`service`, `professional`, and `fringe`. `professional` is the spec's own word (FR-032
requires "one career from the professional tier"); the other two are this project's labels
and the file says so in a comment.

## R6: The eight careers that ship, and what each one proves

**Decision**: the six the Draft table names, plus Drifter, plus Merchant.

| File | Commission and advancement | Medical tier | What it is here to prove |
|---|---|---|---|
| `aerospace-defense.toml` | both | service | Draft row 1 |
| `marine.toml` | both | service | Draft row 2 |
| `maritime-defense.toml` | both | service | Draft row 3 |
| `navy.toml` | both | service | Draft row 4; already shipped, brought to schema v2 |
| `scout.toml` | **neither** | service | Draft row 5; FR-009's two skill rolls a term, declared by the absence of both throws rather than by a flag; a rank-zero bonus on a ladder that names no title |
| `surface-defense.toml` | both | service | Draft row 6 |
| `drifter.toml` | **neither** | fringe | FR-006's always-available flag and FR-015's re-enterable flag; the fringe tier; and a rank zero that grants no bonus at all, which is the only career in the source material where that is true |
| `merchant.toml` | both | professional | The professional tier; a civilian rank ladder, so rank titles are proved not to be a military-only shape; the lowest re-enlistment target in the source, which is what spreads term counts for SC-006 |

**Rationale**: FR-032 fixes six of the eight by requiring every name in the Draft table to
resolve, and fixes a seventh by naming Drifter. The eighth is the only free choice, and
FR-033 constrains it to whatever completes the coverage: the service tier and the fringe
tier are already covered, so the eighth must be professional. Among the thirteen careers in
that tier, Merchant was chosen over Physician, Scientist, and Agent because its rank ladder
is civilian, which is a shape nothing else in the set exercises, and over Noble because the
Noble ladder's rank titles are themselves noble titles, and noble titles are out of scope
(FR-048), so that career would put the one collision the renderer must not have to resolve
into the shipped data.

**Verified**: the shipped set covers every row of the Draft table, both commission shapes,
all three medical tiers, and both Drifter flags, which is exactly SC-008's list.

**Naming trap**: the Draft table in the source writes three of the six careers with a
parenthetical alias that does not match the spelling in the career tables. FR-005 requires
every name the Draft table gives to resolve to a career in force, so the shipped draft
table uses the career-table spellings and nothing else.

## R7: Golden files for a tab-separated format

**Decision**: the npc golden files are read and compared as **bytes**, through a new
`read_golden_bytes` fixture, against `stdout.encode("utf-8")`. `.gitattributes` marks
`tests/golden/npc_*.txt` so that no tool rewrites their line endings.

**Verified**: `Path.read_text(encoding="utf-8")` opens in universal-newline mode, so a
golden checked out with CRLF is read back as LF and compares equal to LF output. Every
existing golden was dumped byte by byte and holds zero tabs and zero carriage returns; all
their alignment is spaces produced by `str.ljust`. The existing text comparison has
therefore never had to detect a whitespace class it could confuse.

**Rationale**: the Universal Character Format is tab separated and FR-046 fixes exactly one
tab between fields. A comparison that cannot tell a tab from spaces, or LF from CRLF,
cannot pin the format at all, and the failure mode is a suite that passes on one platform
and produces a wrong sheet on another. `.gitattributes` already pins LF repository-wide,
which settles it at the source; comparing bytes is what makes the golden prove it rather
than assume it.

**Consequence**: `read_golden` stays as it is for the existing goldens. Adding a second
fixture rather than converting the first keeps this feature from touching evidence SC-014
depends on.

## R8: Locale independence, and how to actually test it

**Decision**: the sort key is `(text.casefold(), text)`. Two checks prove it, and the
guard is the one that matters.

1. **A guard asserts that nothing under `src/` imports `locale`.** This runs everywhere,
   every time, and it is what makes SC-012 unfalsifiable by omission.
2. **A subprocess comparison** runs the same seed with `LC_ALL` set to a locale whose
   collation differs from the default, with the child calling
   `locale.setlocale(locale.LC_ALL, "")` before generating, and compares bytes. It skips
   with a reason when the locale is not installed.

**Rationale**: `str.casefold` is locale-independent by definition in Python, so a
subprocess test that merely sets an environment variable proves nothing: Python does not
call `setlocale` at startup, and the comparison would pass on a build that used
`locale.strxfrm` throughout. SC-012 asks for the cross-locale comparison and it is
provided, but the guard is what actually forbids the mistake. The casefold-plus-codepoint
key is stronger than `lower()` for the same reason: it folds cases `lower()` leaves
distinct, and the codepoint tie-break keeps the order total so two entries that casefold
alike still sort deterministically.

**Alternatives considered**: `locale.strcoll` with a fixed locale, rejected because the
locale would have to be installed on every machine that runs the suite, and Windows names
locales differently. `sorted(key=str.lower)`, rejected because it is not a total order and
leaves ties resolved by list position.

## R9: Two licensing designations, and the notice that has to tell them apart

**Decision**: every shipped data file carries exactly one designation line. Open Game
Content files keep the existing one; name tables carry a new one naming the GPL. The
Section 15 game-data notice is narrowed to name the directories that hold Open Game Content
rather than the whole data tree, and it keeps the parseable shape the existing check
depends on.

**Verified** by reading the checks as they stand:

- `tests/conftest.py` parses the last Section 15 notice with `_NOTICE_PATH`
  (`\(([^()]+)\)`, every parenthesized path) and `_NOTICE_SUFFIX`
  (`every (\.[a-z0-9]+) file`, one extension). Both must keep matching.
- `_uncovered` in `tests/unit/test_licensing.py` and again in
  `tests/guards/test_packaging.py` requires a designated file to end with the covered
  suffix and start with one of the covered paths.
- `_assert_shipped_rules_data` in `tests/guards/test_packaging.py` asserts
  `"Open Game Content" in text` of **every** `.toml` under the data directory in the wheel
  and in the sdist. This is the check that fails on the first name table.
- `DESIGNATION` is written as two adjacent bytes literals in both modules so the test
  source does not designate itself, and `_NOT_SHIPPED` excludes `__pycache__` so a compiled
  copy of the test module does not either.

**What changes:**

1. The notice's parenthesized paths become the OGC subtrees rather than the data root, so
   `_NOTICE_PATH` still yields a tuple of covered prefixes and `_uncovered` still works
   unchanged. `SECTION_15_NOTICES[-1]` in `conftest.py` is updated in the same commit as
   `LICENSE-OGL.txt`, because the check compares them whitespace-normalized.
2. A second designation constant is added, assembled from two adjacent literals for exactly
   the reason the first one is.
3. `_assert_shipped_rules_data` becomes an exactly-one-of-two check. A file carrying both
   is a failure and a file carrying neither is a failure, which is SC-015's wording.
4. `_uncovered` is extended with its mirror: every **GPL-designated** file must be claimed
   by neither the notice's paths nor its suffix. A name table that drifted into an OGC
   directory then fails rather than passing quietly.
5. `DESIGNATION` and `_uncovered` are hoisted into `conftest.py` first, as a structural
   change, because a constant that has to be edited in two places is one that will be
   edited in one.

**SC-015a is what makes all of this fail-able.** The existing
`test_the_coverage_check_sees_a_designated_file_the_old_scan_missed` already writes real
files into the repository and unlinks them in a `finally`. It gains a sibling for each
designation: add an OGC file outside the covered subtrees and the coverage check must fail;
add a GPL-designated file inside them and the mirror check must fail. A check that passes
unchanged when a file is added is the failure FR-042a exists to prevent.

**README and CONTRIBUTING both state the old rule in prose** and both become false when the
first name table lands. They change in the same commit.

## R10: The source material against itself, and against the specification

Eleven places where the two disagree. Each is settled here, and each says which side won.

| # | Conflict | Settled |
|---|---|---|
| 1 | Drifter's prose says the career is always open; its stat table gives it a Dex 5+ qualification throw. | Both. The spec's Assumptions already resolve it: thrown for when selected normally, automatic when entered as the fallback (FR-006). The career file declares the throw **and** the always-available flag, and the walk reads which route it arrived by. |
| 2 | A natural 12 on re-enlistment forces another term, overriding the seven-term cap. | **The spec wins.** FR-014 says a character at the cap musters out "regardless of either". Excluding the override also keeps the aging table's bottom band unreachable, which is what the source's own arithmetic implies for a capped character. |
| 3 | A failed survival throw kills. | **The spec wins**, and the source's own optional rule is the mechanism: the Survival Mishaps table (FR-019, FR-022). |
| 4 | The mishap term costs "half a term, two years", but the checklist adds four years unconditionally. | **The spec wins.** FR-020 and the spec's Assumptions fix two years for a mishap-ended term, still counting toward the cap and the aging modifier. |
| 5 | Mishap row 5 adds four years in prison on top of a term the same rule says lasts two. | Both, additively: the mishap term costs its two years and the row's four are a further effect the row declares. Recorded in data, not in code. |
| 6 | "You lose the benefit roll for the current term only" against two mishap rows that say "lose all benefits". | The specific governs the general, which is the principle the spec already applies to the benefit count. The general rule forfeits the term's roll (FR-020); rows 4 and 5 declare a stronger effect and it is carried in the data rather than in the engine. |
| 7 | The benefit count: the checklist says one per full term plus unquantified extras for higher rank; the specific rule quantifies rank 4, 5, and 6 as one, two, and three extra. | **The specific rule**, which is the spec's own Assumption and FR-016. The rank bonus is not cumulative: rank 6 gains three, not six. |
| 8 | Background skills: "3 + Education DM (1 to 5)" while Education 15 would give 6. | Unreachable and therefore moot: a characteristic rolled on `2d6` tops out at 12, giving a DM of +2 and a count of 5. The engine computes `base + EDU DM` from data and imposes no ceiling of its own. |
| 9 | "The first two have to be taken from your homeworld", against a character entitled to exactly one background skill. | **The spec wins**, and states the answer outright: one background skill means one homeworld skill (FR-003, spec Assumptions). |
| 10 | The homeworld tables cover four of the five law-level descriptors and fourteen of the eighteen trade codes. | Not a conflict this feature has to resolve: homeworld generation is out of scope, so the tables are drawn over directly (FR-003) and the rows that exist are the whole population. The gap is a property of the source, recorded so a later feature that generates worlds knows to find it. |
| 11 | The qualification penalty applies "for each previous career you have entered" in one place and "in which you have served" in another. | **Entered.** A career the character was drafted into and immediately mishapped out of was entered, and reading it the other way would make the draft a way to avoid the penalty. |

## R11: What the source material has that this feature deliberately does not build

Recorded so review does not read them as oversights. Each is a real rule in the source, and
each is left out with a reason.

- **The zero-level sibling rule for cascade skills.** Taking a level in one specialization
  gives every other specialization of that skill level zero. Excluded: FR-011 and the
  spec's own edge case describe the cascade rule as exactly the choice of a specialty and
  nothing further, and adding it would put a rule in engine code that no requirement names
  while turning one skill roll into as many as six printed entries. It is expressible in
  data later without a schema change.
- **Nested cascades.** The source's `Vehicle` cascades to `Aircraft` and `Watercraft`,
  which are themselves cascade skills. Excluded: the skills registry is a flat name to
  specialties mapping, fixed by the previous feature's contract, and `SkillReference` holds
  one optional specialty. Recursing would need a schema change no requirement asks for.
  Choosing `Vehicle` yields `Vehicle (Aircraft)` and stops.
- **Anagathics, and the second survival check they impose.** Out of scope in the spec.
- **The nobility title table.** Out of scope (FR-048), and the eighth career was chosen
  partly to keep it out of the shipped data.
- **Starting equipment, and the checklist step that buys it.** Out of scope. The funds line
  is the mustering-out proceeds, after debt.
- **The optional rule that lowers or removes the term cap.** Not built as an option,
  because the cap is already a data value (FR-038) and a referee lowers it by editing the
  file, which is what SC-013 demonstrates.
- **No new error type.** A draft table naming a career that is not in force is a cross-file
  validation problem and fails the load, exactly like two careers declaring one name. A
  characteristic score outside the pseudo-hex range is a `RulesDataError` for the same
  reason `characteristic_dm` already raises one for a score no band covers. A count below
  one, or a name beside a count above one, is a usage error raised by the CLI. Nothing left
  needs a type of its own, and adding one for a path no caller reaches is the speculative
  surface Principle VI rejects.
- **No schema migration machinery** behind the three raised versions. The field is checked
  for equality and nothing more, unchanged from the previous feature.
- **No floor or ceiling on an override's name tables.** FR-043i's sixty and forty bind the
  shipped tables only, and it says so. They are a test over the packaged data, not a schema
  rule.

## R12: Two rules the requirements imply but do not name

Both are recorded here rather than left as design liberties, because the previous feature's
Complexity Tracking showed how easily a load-bearing field ends up unaccounted for.

**The characteristics registry must declare each characteristic's class.** FR-039 requires
the registry to gain the modifier bands and the pseudo-hex letters as "facts about
characteristics". Whether a characteristic is physical or mental is the same kind of fact,
and FR-038 forbids holding it in engine code. It is load-bearing: the aging table says
"reduce three physical characteristics by 2, reduce one mental characteristic by 1" and the
injury table says "one physical characteristic", and neither can be read from data without
it. The field is added to the `characteristics` schema at version 2 alongside the two the
requirement names.

**Skill rolls granted by a successful commission or advancement.** FR-009 fixes the base at
one skill roll a term, two in a career declaring neither throw. The source additionally
grants a further roll on a successful commission and on a successful advancement, and
FR-001 requires the lifepath run end to end with no step skipped. Both counts are held in
`chargen-parameters.toml` as `on-commission` and `on-advancement`, shipped at one each. A
referee reading FR-009 strictly sets them to zero and gets that reading, with no code edit,
which is what makes putting them in data the answer rather than a way of dodging the
question.

## R13: Characteristic floors and the pseudo-hex range

**Resolution**, and it settles a tension between two statements in the spec itself.

The spec says a score outside the range the pseudo-hex letters cover is a data problem and
the run fails naming the score and the range, and that the letters "must cover every score
the rules can produce". It also says a characteristic that falls to zero or below has the
reduction applied and recorded, with no death resulting. Read together, and given that the
source material's letters begin at zero, those two require the letters to cover negative
scores, which no notation in the source provides.

**Settled as follows:**

- The pseudo-hex declaration carries an explicit `minimum` score alongside its ordered
  symbols, so the covered range is data rather than an assumption. The shipped data
  declares `minimum = 0` and thirty-four symbols, covering 0 through 33.
- A reduction that would take a characteristic below the declared minimum takes it to the
  minimum. The rules therefore cannot produce a score the letters do not cover, which is
  what the requirement asks for.
- The history records the reduction the rule called for **and** the amount actually
  applied, so "the reduction is applied and recorded" holds in the only sense that survives
  the arithmetic, and SC-005's traceability check reads both.
- A score above the top of the range fails the run naming the score and the range. It is
  unreachable from the shipped data and exists for an override that declares a shorter
  table.

**Rationale**: the alternative, letting a score go negative and failing the run when it
renders, would make SC-003 fail for some seeds, and SC-003 admits no exclusions. Putting
the floor in data rather than in code keeps a referee who wants symbols for negative scores
able to declare them and get them.

**Verified** against the source: the letters run 0 through 33, skipping I and O so they
cannot be misread as one and zero, and the source separately states that a score may not
drop permanently below one. The floor at zero is therefore looser than the source's own
rule, not tighter, and zero is representable.

## R14: The sampled audits, and how they stay runnable

**Decision**: SC-003 through SC-008 run over one thousand seeds and SC-019 over ten
thousand rolled names, both marked `slow`, with the marker registered in `pyproject.toml`
beside the two that already exist. The inner development loop runs `-m "not slow"`; CI runs
everything.

**Rationale**: the project's own test-first discipline asks for the whole suite after each
step, which stops being true the moment the suite takes minutes. Marking rather than
shrinking is the only option open, because SC-003 fixes the sample at one thousand or more
and forbids excluding any seed. The marker mechanism already exists in `conftest.py`'s
`pytest_collection_modifyitems`, though the two markers there gate on a platform probe
rather than on speed; a `slow` marker needs no probe and is simply registered and selected
against.

**What the audits actually check**, all of it from the character's own fields and its
history's named parts, never from rendered text (SC-005):

- every seed produces a character, alive, with every required field present;
- age equals the starting age plus the years each term cost, by how each term ended;
- every rank held exists on a ladder of a career the character joined;
- every skill traces to a table the character could reach in a term they served, or to a
  grant they were entitled to;
- the benefit rolls taken match the terms served and the rank reached;
- funds are non-negative and debt is separate;
- no consequence appears that no history step produced;
- term counts spread across at least five distinct values with no more than a quarter at
  the cap;
- two-career and three-career characters both occur;
- every row of the Draft table is reached, both Drifter routes are taken, all three medical
  tiers are charged, and both commission shapes are exercised.
