# Phase 0 Research: Ship Names

**Feature**: `012-ship-names` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

Every NEEDS CLARIFICATION raised while filling the Technical Context is resolved here. Three
questions drove the design: where a name draw can sit without disturbing any other seeded
outcome, where the catalogue lives, and how a fiction-tradition name earns its place under
FR-016.

## Part A — How naming stays additive to seeded generation (FR-010a, SC-008)

**Decision**: draw the name as the **last** `Rolls` call in each generation path, immediately
before the `ShipDesign` is constructed.

**Rationale**: `RandomRolls` wraps a single `random.Random` stream (`src/cetools/engine/rolls.py:111`).
Every `check`, `two_d6`, `d6` and `choose` consumes from that one stream in call order, so a seed
determines a *sequence* of draws, not a set of independent per-decision values. Inserting a draw
anywhere but the end shifts every subsequent draw by one position and changes the hull, drives,
fittings and armament a given seed produces — exactly what FR-010a forbids.

Placing the name draw after the last existing draw leaves the prefix of the stream untouched.
`_select_screen` is the last roll on the starship path (`generator.py:381`) and
`_select_small_craft_turret` is the last on the small-craft path (`generator.py:314`); `build_ship`
consumes no randomness. So one `rolls.choose(...)` inserted after each of those two calls is
provably additive: for any seed, every prior draw returns the same value it did before this
feature, and the only difference in the resulting `ShipDesign` is a populated `name`.

**Verification, not assertion**: the invariant is pinned by a checked-in baseline. Before any
implementation, `specs/012-ship-names/baseline/designs.json` was generated at commit `d387b70`
(pre-feature) and holds `dump_design` output for 100 designs — seeds 0–49 on the standard path
and seeds 0–49 on the small-craft path. The SC-008 test regenerates each seed after the change,
clears the name, dumps it, and compares to the recorded string. This turns "naming is additive"
from a claim into a regression test that fails loudly if a future draw is ever inserted mid-path.

**Alternatives considered**:

- *A second, independently seeded RNG for names.* Would make the name draw positionally
  irrelevant, but the `Rolls` protocol deliberately exposes no seed and no sub-stream, and FR-011
  requires the name to come through the same mechanism as every other choice so it can be
  scripted, replayed and audited. Adding a parallel entropy source to dodge an ordering
  constraint that costs nothing to honour is the speculative abstraction the constitution's
  simplicity posture rules out.
- *Draw the name first and re-derive the rest.* Same stream-shift problem, in the other
  direction, and worse: it breaks every pre-feature seed.
- *Hash the seed into a name.* The `Rolls` seam does not expose the seed, and a hash is not a
  roll — it could not be scripted by `ScriptedRolls`, so no test could pin a name by intent.

**Consequence to record**: name selection is `choose(SHIP_NAMES, ...)`, an index into an ordered
tuple. Adding or reordering catalogue entries later changes which name a given seed yields. That
is acceptable and expected — FR-010a constrains seeds pinned *before this feature*, and no seed
had a name before it — but it means the catalogue must be an ordered `tuple`, and it means
existing seeds' names are not a compatibility surface. This is stated in
[contracts/name-catalogue.md](./contracts/name-catalogue.md).

## Part B — Where the catalogue lives

**Decision**: a new module `src/cetools/engine/ships/names.py`, holding the catalogue rows, the
`Tradition` and `BasisKind` enums, and `generate_ship_name(rolls)`.

**Rationale**: this mirrors the two naming modules the codebase already has —
`engine/names.py` (character names: two data tuples plus `generate_name`) and
`engine/worlds/naming.py` (`generate_world_name`) — so a reader looking for "where do names come
from" finds the same shape in all three domains. `generate_ship_name` is exported from
`cetools.engine.ships` alongside `generate_ship`, satisfying Library-First: a caller can draw a
ship name without generating a ship and without touching the CLI.

**Alternatives considered**:

- *Add `SHIP_NAMES` to `engine/ships/tables.py`.* Rejected on provenance: that module's docstring
  scopes it to "SRD Chapter 8 tables", and every row in it is traceable to a printed table. Ship
  names appear nowhere in the SRD. Mixing invented content into the SRD-fidelity module would
  blur the one boundary Principle I depends on. It is also already 1162 lines.
- *A TOML or JSON data file loaded at import.* Rejected as unnecessary I/O and an unnecessary
  packaging concern (`package-data` wiring, a parse path, a failure mode at import). A frozen
  dataclass tuple is data-driven in exactly the sense Principle V means: adding a name is a
  one-line edit to a literal, with no engine logic touched.
- *Inline the catalogue in `generator.py`.* Rejected: it would put 160 lines of content into the
  module that holds the selection rules, and would make `generate_ship_name` untestable without
  generating a ship.

## Part C — The FR-016 sourcing test, applied

The spec's Resolved Decisions section fixes the policy: a fiction-tradition name is catalogued
only if it stands on its own outside its source work, and every such entry records the basis that
qualifies it. Research here settles how that policy is *operated*.

### C1 — The three basis kinds, and what evidence each requires

| Basis kind | What qualifies | Reference field records |
|------------|----------------|-------------------------|
| `ORDINARY_WORD` | The name is a common English noun or adjective in ordinary use, with a meaning independent of any fiction. | The word's ordinary sense, e.g. `"serenity: calm, untroubled state"` |
| `REAL_VESSEL` | A real historical ship of that name existed. | The vessel, e.g. `"HMS Endeavour, 1764"` |
| `PUBLIC_DOMAIN_WORK` | The source work borrowed the name from literature now in the public domain. | The work and author, e.g. `"Rocinante, Cervantes, Don Quixote (1605)"` |

A name may satisfy more than one test (*Nautilus* is both a Verne borrowing and a real US Navy
submarine). One basis is recorded — whichever is most direct — because the field is evidence that
the constraint holds, not an exhaustive provenance record. One is enough to clear FR-016.

### C2 — Tradition is assigned once, by earliest origin

A name can plausibly belong to two traditions: *Pegasus* is Greek myth and also a vessel in
screen science fiction; *Prometheus* likewise. FR-009 forbids duplicate names, so each name is
catalogued exactly once, under the **earliest tradition it belongs to**. Myth and folklore
therefore absorb every mythological name regardless of who later flew a ship under it.

This is not a bookkeeping detail — it materially shapes the fiction traditions. Because
mythological borrowings are claimed by myth/folklore, and coined names are excluded by FR-016,
the written-SF and screen-SF entries lean overwhelmingly on `REAL_VESSEL` and `ORDINARY_WORD`
bases. That is the intended result: those are precisely the names that carry no franchise
association.

### C3 — Feasibility check

FR-008 requires ≥150 entries with ≥20 per tradition; SC-005 caps any one tradition at half the
catalogue. The binding constraint is the fiction traditions, so both were sampled before
committing to a target.

**Mythology and folklore** — unconstrained by FR-016; the tradition is its own warrant. Greek,
Norse, Arthurian, Celtic, Mesopotamian, Japanese, Chinese, West African and Mesoamerican sources
between them offer several hundred candidates well past the target (Beowulf, Achilles, Perseus,
Hyperion, Nemesis, Valkyrie, Sleipnir, Fenrir, Yggdrasil, Excalibur, Durendal, Gawain,
Cu Chulainn, Gilgamesh, Marduk, Amaterasu, Susanoo, Qilin, Garuda, Simurgh, Anansi, Quetzal, …).
Depth is not in question; the work is curation and unaccented spelling (FR-018).

**Written science fiction** — sampled across Verne, Clarke, Heinlein, Anderson, Cherryh, Bujold,
Weber, Drake and Corey. Naval-tradition names are abundant because the genre's own convention is
to borrow them: *Nautilus* (Verne; also USS Nautilus), *Albatross* (Verne; ordinary word),
*Endeavour* (Clarke; HMS Endeavour), *Rocinante* (Corey; Cervantes), *Canterbury* (Corey; HMS
Canterbury), *Razorback* (Corey; ordinary word), *Behemoth* (Corey; Book of Job), *Skylark*
(Smith; ordinary word), *Fearless* / *Reliant* / *Invincible* / *Agamemnon* (Weber; all Royal Navy
names), *Norway* / *Pacific* / *Europe* (Cherryh; real places and real vessels), *Ariel* (Bujold;
Shakespeare), *Peregrine* (ordinary word). Comfortably past 40 qualifying candidates.

**Science fiction film and television** — the pool is smaller but sufficient, and its shape is
exactly what the spec predicted. Star Trek alone contributes a long run of real-vessel names
(*Enterprise*, *Defiant*, *Excelsior*, *Intrepid*, *Constitution*, *Lexington*, *Yorktown*,
*Saratoga*, *Hornet*, *Valiant*, *Repulse*, *Bellerophon*, *Potemkin*, *Farragut*) and ordinary
words (*Voyager*, *Sovereign*, *Ambassador*, *Nebula*, *Galaxy*). Beyond Trek: *Nostromo* and
*Narcissus* (Conrad, public domain), *Serenity* (ordinary word), *Liberator* (real vessel),
*Swordfish*, *Bebop*. Star Wars contributes almost nothing — *Devastator*, *Avenger* and
*Relentless* are Royal Navy names; *Millennium Falcon*, *Tantive IV* and *Executor* are coined and
excluded. That cost is the one the spec's Resolved Decisions section already accepted.

**Decision**: target **160 entries — 76 mythology and folklore, 42 written science fiction, 42
science fiction film and television.** This clears the 150 floor with headroom, clears the
per-tradition floor of 20 by a factor of two, and puts the largest tradition at 47.5%, inside the
50% cap with room for the catalogue to grow.

**The tests assert the floors, not these counts.** `>= 150`, `>= 20` per tradition, `<= 50%` for
the largest. Pinning exact counts would make every future name addition a test edit, which is the
opposite of Principle V.

## Part D — Rendering, export and round-trip come free

**Finding**: FR-012, FR-013, FR-014 and FR-015 require no new code.

`ShipDesign.name` already exists as an optional field (`models.py:389`). `_ship_name` already
renders it into the heading and the first sentence, falling back to `"Unnamed Ship"` only when it
is absent or blank (`description.py:66`). `dump_design` already emits `name = ...` when set
(`design.py:349`), and `load_design` already reads it (`design.py:272`), so the round-trip
`build_ship(loads_design(dump_design(design)))` carries the name through unchanged. `build_ship`
never writes a name, so building from a file stays deterministic and file-driven (FR-015), and a
name the generator did not set is one an author supplied — which the generator never sees, since
it constructs its own design (FR-014).

The consequence is that this feature's entire footprint in existing code is two `ShipDesign(...)`
call sites in `generator.py` gaining a `name=` argument, and one new `RollName` member. Everything
else is new content and new tests.

**Rejected alternative**: naming inside `build_ship` so that any nameless design acquires one.
Directly contradicts FR-015 and would make building non-deterministic.

## Part E — What the catalogue may contain (FR-017, FR-018)

**Decision**: entries are bare ASCII proper names carrying no ship-type designation, validated by
test rather than by review.

- **Unaccented (FR-018)**: every entry must satisfy `str.isascii()`. "Sigurd", not "Sigurðr";
  "Cu Chulainn", not "Cú Chulainn". This keeps a name byte-identical across a rendered
  description, a TOML export and any terminal encoding.
- **Bare names (FR-017)**: no entry may begin with a ship-type designation — *Free Trader*,
  *Scout*, *Yacht*, *Corsair*, *Liner*, *Courier*, *Merchant*, *Cruiser*, *Frigate*, *Destroyer*,
  *Carrier*, *Transport*, *Shuttle*, *Tender*, *USS*, *HMS*, *ISS*, *SS*. The ship's type,
  configuration and role are already stated by the description's own sentences; a prefix would
  duplicate them and would be wrong whenever the generated hull is not that type. Tested against
  a deny-list of designation prefixes.
- **Renderable (existing constraint)**: `_validate_author_prose` (`models.py:267`) rejects a name
  with leading, trailing, doubled or non-space whitespace, because the description is one
  unwrapped paragraph. Catalogue entries must pass it; a test runs every entry through
  `ShipDesign` construction to prove they all do.
- **No duplicates (FR-009)**: compared case-sensitively on the exact spelling, since that is what
  renders. A test asserts `len({e.name for e in SHIP_NAMES}) == len(SHIP_NAMES)`.

## Part F — SRD fidelity

The Cepheus Engine SRD's Chapter 8 "Ship Design and Construction" and Chapter 9 worked examples
name individual vessels in prose but publish **no ship-name table and no naming rule**. There is
therefore no SRD rule to be faithful to, and none to deviate from. This feature adds no game
mechanic: it populates an existing optional field with curated content, and no computed
value — tonnage, cost, crew, tech level, build time — is touched. Principle I is satisfied
vacuously, and no deviation is recorded.
