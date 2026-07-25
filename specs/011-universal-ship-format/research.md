# Phase 0 Research: Universal Ship Description Format

**Feature**: 011-universal-ship-format | **Date**: 2026-07-24

Sources, verbatim:

- [Ship Design and Construction](https://evolvedexperiment.github.io/cepheus-srd/ship-design-and-construction.html)
  — the Universal Ship Description Format template, and every component table that must
  gain a display name or tech level.
- [Chapter 9: Common Vessels](https://evolvedexperiment.github.io/cepheus-srd/common-vessels.html)
  — 15 starship and 6 small-craft worked examples, the only place the format is shown in
  actual use.

Per the spec's Assumptions and Constitution Principle I, the template is authoritative for
sentence *order*; where the template and the Chapter 9 examples differ in *phrasing*, the
worked examples win. Every deviation from either is recorded below with a reason. Nothing is
invented.

---

## Part A — The SRD template, verbatim

Reproduced exactly as the source page prints it, because every sentence contract in
[contracts/description-format.md](./contracts/description-format.md) is derived from it:

> \[Ship's Tech Level\] \[Ship Descriptive Name\]
>
> Using a \[Ship Hull Displacement\]-ton hull (\[Hull Damage Value\] Hull, \[Structure Damage
> Value\] Structure,), the \[Ship Descriptive Name\] is \[General Description of Ship's
> Function\]. It mounts jump drive \[Jump Drive Code\], maneuver drive \[Maneuver Drive Code\],
> and power plant \[Power Plant Code\], giving a performance of Jump-\[Jump Number\] and
> \[Thrust Number\]-G acceleration. Fuel tankage of \[Fuel Tonnage\] tons supports the power
> plant for \[Weeks of Power\] and \[Number of Jumps\] jump-\[Jump Number\]. \[Any additional
> fuel usage notes.\] Adjacent to the bridge is a computer Model \[Computer Number, followed by
> a slash and bis or fib options noted, if purchased\]. The ship is equipped with \[Sensors
> Type\] sensors (\[Sensors DM\].) There are \[Number of Staterooms\] staterooms and \[Number of
> Low Berths\] low berths. The ship has \[Number of Hardpoints\] hardpoints and \[Fire Control
> Tonnage\] tons allocated for fire control. Installed on the hardpoints are \[Describe number
> and type of turrets, and any weapon systems that have been installed, if any. Also note any
> ammunition carried for missiles and sandcasters.\] This ship has \[Number of Screens
> Installed\] screens: \[Describe number and type of screens\]. There are \[Number of Small
> Craft Hangers\] small craft hangars, \[Describe number and contents of each hangar\]. Cargo
> capacity is \[Cargo Tonnage\] tons. The hull is \[Hull Configuration\], and is armored with
> \[Armor Type\] (\[Armor Rating\] points.) \[Note any Ship's Armor options that have been
> installed.\] Special features include \[List additional components here, included fuel
> processors and fuel scoops\]. The ship requires a crew of \[Crew Total\]: \[List crew
> positions\]. The ship can carry up to \[Double the Number of Non-Crew Staterooms\] additional
> passengers at double occupancy and \[Number of Low Berths\] low passengers. The ship costs
> MCr\[Cost of Ship\] (including discounts and fees) and takes \[Construction Time\] weeks to
> build.

This fixes the sixteen-sentence order required by FR-004. Three template artefacts are
corrected against the worked examples, which never reproduce them:

| Template artefact | Corrected to | Why |
|---|---|---|
| `Structure,)` — stray comma | `Structure)` | No Chapter 9 example prints it; it is a typo. |
| `(… DM.)` and `(… points.)` — period inside the parenthesis | `(…).` | No Chapter 9 example prints it. |
| `allocated for fire control` | `allocated to fire control` | All 20 starship examples print "to"; only the small-craft examples print "for". Starships are the majority case. |

---

## Part B — Sentence templates, from the worked examples

Every clause below is quoted from a Chapter 9 vessel. The full per-sentence contract, with
omission rules and singular/plural forms, is
[contracts/description-format.md](./contracts/description-format.md); this part records only
where the wording comes from.

| # | Sentence | Quoted source |
|---|---|---|
| 1 | Hull and purpose | "Using a 200-ton hull (4 Hull, 4 Structure), the Asteroid Miner is frequently used to exploit…" |
| 2 | Drives | "It mounts jump drive A, maneuver drive A, and power plant A, giving a performance of Jump-1 and 1-G acceleration." |
| 3 | Fuel | "Fuel tankage of 44 tons supports the power plant for four weeks and two Jump-1 jumps." |
| 4 | Computer | "Adjacent to the bridge is a computer Model 3/fib." |
| 5 | Sensors | "The ship is equipped with Basic Civilian sensors (DM-2)." |
| 6 | Quarters | "There are three staterooms and five low berths." |
| 7 | Hardpoints | "The ship has two hardpoints and two tons allocated to fire control." |
| 8 | Weapons | "Installed on the hardpoints are two triple turrets armed with missiles and one triple turret armed with beam lasers." + "120 smart missiles are carried as ammunition for the missile turrets." |
| 9 | Screens | "In addition, this vessel has two screens: a meson screen and a nuclear damper." |
| 10 | Hangars | "There are two small craft hangers, each holding a fighter (also included in the ship's cost)." |
| 11 | Cargo | "Cargo capacity is 84 tons." |
| 12 | Configuration and armour | "The hull is standard, armored with Crystaliron (8 points), and possesses a stealth coating…" |
| 13 | Special features | "Special features include an armory, four detention cells, five tons of fuel processors (processes 100 tons of unrefined fuel into refined fuel per day) and fuel scoops." |
| 14 | Crew | "The ship requires a crew of three: one pilot, one navigator and one engineer." |
| 15 | Passengers | "The ship can carry up to four additional passengers as prisoners…" / "The ship cannot carry any additional passengers." |
| 16 | Cost | "The ship costs MCr33.219 (including discounts and fees) and takes 44 weeks to build." |

### Decisions taken where the examples offer a choice

**Decision — fuel sentence uses the "supports the power plant for N weeks" form.**
Rationale: two forms appear ("supports the power plant for four weeks and two Jump-1 jumps"
vs. "supports four weeks of power plant operation and one Jump-2 jump"). The first is what
the template prescribes ("supports the power plant for \[Weeks of Power\]"), so template and
majority agree. Alternatives considered: alternating by ship class (arbitrary); emitting the
second form (contradicts the template).

**Decision — a computer's options render as `/bis`, `/fib`, or `/bis/fib`.**
Rationale: the Ship Computer Options section names Jump Control Specialization **(bis)** and
Hardened Systems **(fib)**, and states "Both options can be applied to the same computer".
`ComputerFit.jump_control` is `bis`; `ComputerFit.hardened` is `fib`. No example shows both,
so `/bis/fib` is the template's own phrasing ("a slash and bis or fib options noted") applied
to the documented both-options case. Alternatives considered: inventing a third suffix
(forbidden — no SRD basis).

**Decision — weapon bays are listed before turrets in the weapons sentence.**
Rationale: every example that carries both prints bays first ("ten fusion gun bays, five
missile bays and 35 triple turrets…"; "one particle beam bay, three triple turrets…"). The
spec's Assumptions already place bays in this sentence.

**Decision — the hangars sentence states each hangar's tonnage capacity, not its contents.**
Rationale: FR-014 asks for capacity. The SRD examples name the craft carried ("each holding a
fighter") because their designers chose them; `FittingFit` records `vehicle_tons` only, and
inventing a craft name would violate Principle I. "There are two small craft hangars, each
holding 20 tons of small craft" states exactly what the design determines.

**Decision — the screens sentence drops the examples' "In addition," connective.**
Rationale: Chapter 9 prints "In addition, this vessel has two screens: a meson screen and a
nuclear damper", but "In addition" presupposes the installed-weapons sentence immediately
before it. FR-021 omits that sentence for a screened ship carrying no turrets or bays, which
would leave the connective dangling — exactly what FR-021a forbids. The template's own "This
ship has \[Number of Screens Installed\] screens:" is used instead. This is the
worked-examples-win assumption yielding to a grammar rule, the same way FR-019a yields to
Chapter 8's rule on emergency low berths. Alternatives considered: emitting "In addition,"
only when the weapons sentence is present (makes one sentence's wording depend on another's,
which the omission design explicitly forbids — see data-model.md §6).

**Decision — an unarmed ship keeps the SRD's "but has no weapons installed" clause.**
Rationale: the Courier, Merchant Freighter and Yacht all print "The ship has one hardpoint and
one ton allocated to fire control, but has no weapons installed." This satisfies FR-021 (no
separate installed-weapons sentence) *and* SC-004 (every applicable SRD sentence pattern
appears) with one clause rather than a negation sentence.

---

## Part C — Number and text style

The SRD is not internally consistent here, and the spec's clarification session (FR-022,
FR-022a) plus a follow-up decision during planning settle it. Recorded per Principle I.

**Evidence.** Counts of things are written as words at small magnitudes and as digits at
large: "a crew of three", "a crew of 18", "twelve staterooms", "25 staterooms", "fifty
hardpoints", "35 triple turrets". Measured and rated values are digits at every magnitude:
"a 100-ton hull (2 Hull, 2 Structure)", "Jump-2", "6-G", "(DM+1)", "(8 points)", "TL11",
"Model 3/fib", "MCr194.445". Tonnage *in running prose* is the exception that FR-022a did not
anticipate: every example writes "two tons allocated to fire control", "three tons of fuel
processors", "eight tons allocated to fire control" — words, not digits.

**Decision — three rules, applied by `prose.py`:**

1. **Counts of things** (crew, staterooms, low berths, hardpoints, turrets, bays, screens,
   hangars, fittings, jumps, weeks of power, passengers): word for 0–10 ("zero", "one", …,
   "ten"), digits above ten. (FR-022.)
2. **Tonnage stated in running prose** (fire-control tons, cargo tons, fuel tankage, fuel
   processor tons, hangar capacity): same rule as counts when the value is a whole number;
   digits whenever it is fractional. So "two tons allocated to fire control", "84 tons",
   "1.3 tons", "zero tons".
3. **Measured and rated values** are always digits, at every magnitude: the hull sentence's
   `[N]-ton hull`, Hull and Structure points, Jump rating, G-acceleration, sensor DM, armour
   protection points, computer model number, tech level, MCr cost, and build weeks. (FR-022a.)

Rule 2 narrows FR-022a, which as written says tonnage is always digits. The narrowing was put
to the user during planning and chosen deliberately: SC-002 requires the output to read as the
same kind of writeup as a Chapter 9 vessel, and "2 tons allocated to fire control" is a
sentence the SRD never prints. Recorded as a spec amendment in
[plan.md](./plan.md#constitution-check). The zero-cargo edge case's quoted "Cargo capacity is
zero tons" is consistent with rule 2 and is kept verbatim.

Build weeks are unaffected in practice: the smallest tabulated build time is 28 weeks, so rule
1 and rule 3 agree on every buildable ship.

**Decision — words above ten are digits, departing from the SRD in the 11–99 band.**
Rationale: the SRD itself is inconsistent there ("twelve staterooms" but "25 staterooms";
"fifty hardpoints" but "a crew of 18"), so no consistent rule can be extracted. FR-022 fixes
the boundary at ten. Alternatives considered: matching the SRD example-by-example (not a rule,
and unimplementable); spelling everything (contradicts "a crew of 18").

**Decision — MCr costs carry thousands separators; tonnage does not.**
Rationale: the cost sentence is consistent across all 20 examples ("MCr2,768.145",
"MCr1,146.915"). Tonnage is not ("a 5000-ton hull" but "Fuel tankage of 1,096 tons"), so the
simpler rule is taken for tonnage.

**Decision — MCr and tonnage render at a fixed six decimal places, then have trailing zeros
stripped; never scientific notation.**
Rationale: FR-025, FR-025a and the fractional-cost edge case. Python's `:g` — used by the
outgoing sheet — fails on three counts: it caps at six *significant* figures, so `2768.145`
becomes `2768.14`; it switches to scientific notation above 1e6; and it hides nothing about
binary floating point at the boundary. Formatting at fixed precision first also suppresses the
artefact a summed cost produces — the Beowulf's total is accumulated from a dozen floats and
must print `MCr29.772`, not `MCr29.771999999999998`. Six places is below the smallest figure
the SRD prices (a standard missile at Cr1,250 = MCr0.00125) and above any artefact. The SRD's
own "MCr597.870" keeps a trailing zero; FR-025 explicitly overrides that, so cetools prints
`MCr597.87`.

**Decision — the hull sentence's article is "an" when the tonnage's leading digit is 8, else
"a".**
Rationale: "Using an 800-ton hull" (Destroyer) against "a 100-ton", "a 200-ton", "a 1000-ton",
"a 5000-ton", "a 50-ton", "a 10-ton". Eight is the only leading digit whose spoken form begins
with a vowel among the tabulated hull sizes. Alternatives considered: a full
number-to-words-then-vowel check (unnecessary for a bounded table of 18 starship and 18
small-craft sizes).

**Decision — lists of two or more items join with commas and a final "and", no serial comma.**
Rationale: FR-024, and the examples: "one pilot, one navigator and one engineer"; "an armory,
four detention cells, five tons of fuel processors … and fuel scoops".

---

## Part D — Tech level: which categories the SRD tabulates

FR-028a requires every category the SRD assigns a tech level to contribute to the derived
value, and forbids inventing one where the SRD states none. Each ship-design table was read
column by column. This is the finding, not an omission list:

| Category | SRD tech level | Values |
|---|---|---|
| Ship Hull by Displacement | **None** — the table has Hull, Hull Code, Price, Construction Time and no TL column | — |
| Ship Configuration | **None** | — |
| Drive Costs (J/M/P) | **None** — the table has Drive Code, Tons, MCr only | — |
| Small Craft Hull / Drive Costs / Cockpits | **None** | — |
| Ship Armor by Type | Yes | Titanium Steel 7, Crystaliron 10, Bonded Superdense 14 |
| Ship Armor Options | Yes, in prose | Reflec 10, Self-Sealing 9, Stealth 11 |
| Ship Computer Models | Yes | Model 1–7 → TL 7, 9, 11, 12, 13, 14, 15 |
| Ship Electronics | Yes | Standard 8, Basic Civilian 9, Basic Military 10, Advanced 11, Very Advanced 12 |
| Turret Displacement and Cost | Yes | Single 7, Double 8, Triple 9, Pop-up 10, Fixed Mounting **"-"** (none) |
| Turret Weapons | Yes | Missile Rack 6, Pulse Laser 7, Sandcaster 7, Particle Beam 8 |
| Missile Types | Yes | Standard 6, Nuclear 6, Smart 8 |
| Sandcaster barrels | Yes, in prose | "can be manufactured at TL5" |
| Bay Weapons | Yes | Missile Bank 6, Particle Beam 8, Meson Gun 11, Fusion Gun 12 |
| Screens | Yes | Meson Screen 12, Nuclear Damper 12 |
| Additional Ship Components (armory, detention cell, fuel scoops, fuel processor, laboratory, library, luxuries, vault, hangar) | **None** — all described in prose with no TL | — |
| Ship Software | A **floor**, not a value ("9+", "10+") | Excluded |

**Decision — hulls, drives, configurations, cockpits, quarters and fittings carry no `tl`
column and contribute nothing.**
Rationale: FR-028a's closing sentence. Adding a column the SRD does not fill would be
inventing data. Alternatives considered: deriving a hull TL from build cost (fabrication);
assuming TL 9 as a floor for civilian hulls (fabrication).

**Decision — Ship Software is excluded from the derived tech level.**
Rationale: the table's TL column is a per-level floor ("TL is the same as the TL required for
a given Jump number"), not a fixed value for the row, and FR-028a's enumeration does not name
software. Alternatives considered: treating "9+" as 9 (understates a Jump-4 tape; also invents
a rule the SRD does not state).

**Decision — the derived tech level has a floor of 8, because every ship carries Standard
electronics.**
Rationale: the Ship Electronics table lists Standard at TL 8 with tons and cost both "Included
in bridge", and every Chapter 9 vessel with no purchased package — including the small craft,
which have a cockpit rather than a bridge — prints "Standard sensors". So a design with
`electronics = None` still carries the Standard package, and `Ship.tech_level` is always an
`int`, never absent. This also supplies FR-009's sensors sentence for such a design.
Alternatives considered: an optional tech level and a heading without a `TL` prefix (reachable
only by ignoring a package the SRD says every ship has); a hardcoded floor constant (the value
would duplicate `ELECTRONICS["standard"].tl`).

**Decision — the fixed mounting contributes no tech level.**
Rationale: its TL cell is literally "-". `MountRow.tl` is `int | None`, and `None` contributes
nothing — the same treatment as an untabulated category, expressed per row.

---

## Part E — Display names in the rules data

FR-030 and FR-031 require every component the paragraph can name to carry its SRD prose
spelling on its own data row, so the renderer never spells a component and a new SRD row is a
data-only edit.

**Decision — nameable rows carry `name`; rows that appear after a count also carry `plural`,
spelled explicitly rather than derived.**
Rationale: the SRD's plurals are not uniformly regular — "armory" → "armories", "laboratory" →
"laboratories" — so a renderer-side `+ "s"` would be logic that a new SRD row could silently
break, defeating SC-007. Two explicit columns keep every spelling in data. Alternatives
considered: an inflection helper (adds a dependency and still guesses); a single column plus a
suffix rule (breaks on "armories").

**Decision — a fitting's `name` column carries its indefinite article; its `plural` does
not.**
Rationale: the special-features list mixes countable and mass nouns — "an armory", "four
detention cells", "fuel scoops" — and "fuel scoops" takes no article and no count at quantity
one. Storing "an armory" / "armories" and "fuel scoops" / "fuel scoops" renders all three
correctly from one rule (`count == 1 → name`, else `count word + plural`) with no per-kind
branch in the renderer.

**Decision — turret weapons are named for the armament clause, not the catalog.**
Rationale: the examples write "armed with missiles", never "armed with missile racks". So
`TURRET_WEAPONS["missile_rack"].name` is "missile", `plural` "missiles". The same singular
also spells the ammunition sentence's "the missile turrets" and "the sandcaster turrets", so
one pair of columns serves both clauses.

**Decision — sandcaster ammunition is called "canisters".**
Rationale: Chapter 8 calls them barrels; Chapter 9 prints "100 canisters are carried as
ammunition for the sandcaster turrets". The spec's Assumptions make the worked examples
authoritative for phrasing. The design-schema key `sand_barrels` is unchanged — it is an input
identifier, not prose, and FR-033 requires the round trip to stay lossless.

**Decision — `AmmoRow` gains a `weapon` column naming the `TURRET_WEAPONS` key it feeds.**
Rationale: the ammunition sentence must name the weapon ("for the missile turrets") and FR-031
forbids the renderer knowing that missiles go in missile racks. One key-valued column makes
the link data.

**Decision — hull configurations are named in lower case.**
Rationale: the starship examples print "The hull is standard" and "The hull is streamlined";
only the small-craft examples capitalise. Starships are the majority case, and mixed casing in
one sentence would read as a defect.

**Decision — the vehicle hangar's display name is "small craft hangar".**
Rationale: the key is `vehicle_hangar`; the SRD prose is "small craft hangars" (misspelled
"hangers" throughout Chapter 9 — corrected, as it is plainly a typo for the template's own
"small craft hangars"). This is the spec's worked example of FR-030.

**Decision — the renderer identifies a hangar by `FittingRow.tons_per_vehicle_ton is not
None`, never by key.**
Rationale: that column already marks a vehicle-sized fitting in `models.py` and `builder.py`;
reusing it keeps the hangars sentence — and the matching exclusion from special features —
data-driven, so a second SRD vehicle-sized fitting stays a data-only edit (SC-007).

**Decision — fuel processors and luxuries are counted in tons, via a `counted_in_tons`
column; fuel processors additionally carry `unrefined_fuel_per_ton = 20`.**
Rationale: the SRD prints "five tons of fuel processors (processes 100 tons of unrefined fuel
into refined fuel per day)" and "two tons of luxuries", against "four detention cells" for
ordinary fittings. FR-017 names the fuel-processor throughput explicitly, so the column is
required, not speculative; 20 tons per ton per day is the Fuel Processors paragraph's stated
rate. Two data columns drive two generic renderer branches — the same idiom
`tons_per_vehicle_ton` already establishes. Alternatives considered: a per-kind branch in the
renderer (violates FR-031); deriving "counted in tons" from `tons == 1.0` (coincidental, and
wrong the moment the SRD adds a one-ton countable fitting).

**Decision — crew position names live in a `CREW_POSITIONS` table in `tables.py`.**
Rationale: they are SRD table content (Table: Ship Crew Requirements lists Position), and
holding them as an ordered tuple of `(field, singular, plural)` fixes both the spelling and
the FR-018 breakdown order in one place. cetools derives seven positions; the SRD's fuller
list (commanding officer, marines, scientists, flight crew) is referee-discretion staffing
that feature 010 deliberately left out of scope, and this feature invents none of it.

---

## Part F — Values the description states that the builder already computes

FR-032 forbids changing any computed value. Every number in the paragraph is read from `Ship`,
`ShipDesign` or a table; the two derivations below are new, and both are presentation-only.

**Decision — fire-control tonnage is reported as the ship's hardpoint count.**
Rationale: all 20 examples report the two as equal, including ships with unused hardpoints
("The ship has four hardpoints and four tons allocated to fire control, but has no weapons
installed", Merchant Freighter). cetools folds a turret's fire control into the turret's own
ton (`MountRow.tons`) and adds a separate ton per bay, so no single `LineItem` sum reproduces
the SRD's figure. Reporting `ship.hardpoints` matches the source exactly and changes no
computed value. Alternatives considered: summing bay fire-control line items (would print
"zero tons" for every turret-armed ship, which no example does); adding a fire-control line
item to the builder (would change tonnage and cost — forbidden by FR-032).

**Decision — passenger capacity is `max(0, staterooms − crew total) × 2` plus `low_berths`.**
Rationale: FR-019's literal text ("the number of additional passengers carried at double
occupancy in non-crew staterooms and the number of low passengers"), matching the template's
"\[Double the Number of Non-Crew Staterooms\]". Both clauses drop when their value is zero;
both zero yields the SRD's "The ship cannot carry any additional passengers."

**Decision — emergency low berths are not offered as passenger capacity.**
Rationale: Chapter 8 states emergency low berths "will not carry passengers, but can be used
for survival", while Chapter 9 prints "four emergency low passengers" for the Courier. This is
a rules contradiction, not a phrasing one, so the worked-examples-win assumption does not
apply and Chapter 8 governs. The spec's own edge case agrees: "the passenger sentence must not
offer capacity the ship does not have". Emergency low berths still appear in the quarters
sentence (FR-010). Alternatives considered: four passengers per emergency berth (contradicts
the rule that states they carry none).

**Decision — the number of jumps is `jump_distance ÷ jump_rating`, floored.**
Rationale: `build_ship` sets `jump_fuel = 0.1 × hull_tons × jump_distance` and the SRD's jump
consumes `0.1 × hull_tons × jump_rating` per jump, so the tankage supports that many jumps at
the rated distance — "two Jump-1 jumps" for the Asteroid Miner's 44 tons on a 200-ton hull.
A design with `jump_distance = 0` yields "zero Jump-1 jumps"; the clause is kept because
FR-007 requires it and the fuel tankage figure would otherwise be unexplained.

**Decision — the drives sentence omits the maneuver clause when no maneuver drive is
fitted.**
Rationale: the SRD permits a starship with a jump drive and no maneuver drive, and
`build_ship` builds one. FR-021's grammar rule then requires "It mounts jump drive A and power
plant A, giving a performance of Jump-1." rather than a "maneuver drive None" fragment. No SRD
example shows this ship, so the sentence is assembled from the template's own clauses.

**Decision — the small-craft computer sentence says "cockpit".**
Rationale: FR-027. The SRD's own small-craft examples print "Adjacent to the bridge is a
computer Model 1" even though the same paragraph says "There is a one-man cockpit" — a slip in
the source, since the small-craft rules replace the bridge with a cockpit. Following the slip
would produce a description that contradicts itself. Recorded as a deliberate deviation in
[plan.md](./plan.md#constitution-check).

---

## Part G — Where the description lives

**Decision — `render_description(ship)` in a new `engine/ships/description.py`, replacing
`render_sheet(ship)` in `engine/ships/sheet.py`, which is deleted.**
Rationale: FR-002 makes USDF the output, not an alternative to the sheet — the feature 006
precedent, where the Universal Character Format replaced the per-characteristic output rather
than joining it. "Sheet" no longer describes a prose paragraph, and the repo's docs gate
requires a rename to travel with the docs that name it. Alternatives considered: keeping
`render_sheet` as the name (misnames the output; CONTEXT.md's "ship sheet" vocabulary would
have to say two things); keeping both renderers (FR-002 forbids it, and a second format
doubles the SC-003 determinism surface for no stated need).

**Decision — number, list and article helpers live in a separate `engine/ships/prose.py`.**
Rationale: FR-022, FR-022a, FR-023, FR-024 and FR-025 are all grammar-and-number rules
independent of any ship, and they carry the majority of this feature's edge cases (crew of
one, zero cargo, fractional cost, three-item joins). A module with no ship knowledge makes
them directly testable without constructing a `Ship`, and keeps `description.py` a readable
list of sentence builders. Alternatives considered: private helpers inside `description.py`
(testable only through a whole paragraph, so a plural bug reads as a rendering failure);
`cetools/formatter.py` (that module is the character formatter and has no ship dependency —
merging domains there would be worse).

**Decision — the derived tech level is computed by `build_ship` and carried on `Ship`.**
Rationale: it is a computed ship value like crew, cost and hull points, and FR-028's override
belongs to the design. Computing it in the builder keeps the renderer free of table walking
and lets FR-028a be tested without rendering a paragraph. `Ship` gains `tech_level: int`;
`ShipDesign` gains `tech_level: int | None`, which the builder uses as given when present
(FR-028b — never re-checked against the derived value).

**Decision — a design with no purpose is described by its hull class.**
Rationale: FR-029a, and Principle I — the builder determines whether a hull is a starship or a
small craft, so "the Beowulf is a starship." asserts nothing invented. A design with no name
uses "Unnamed Ship", the placeholder the outgoing sheet already prints, in both the heading and
the first sentence (FR-029b).
