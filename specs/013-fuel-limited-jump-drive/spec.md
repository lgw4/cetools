# Feature Specification: Fuel-Limited Jump Drive Rating

**Feature Branch**: `013-fuel-limited-jump-drive`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "We have a logic problem in ship generation. If a ship's fuel cannot support one jump at its jump rating, it should be built with a lower rated jump drive."

## Overview

Random ship generation currently picks a jump drive first and buys jump fuel afterwards, out of
whatever tonnage happens to be left. When the leftover tonnage cannot cover a full jump at the
drive's rating, the generator keeps the oversized drive and simply buys partial fuel. The result is
a ship that carries tons of jump fuel it can never use and a description that reads:

> It mounts jump drive C, maneuver drive A and power plant C, giving a performance of Jump-6 and
> 2-G acceleration. Fuel tankage of 56 tons supports the power plant for two weeks and **zero
> Jump-6 jumps.**

A ship that cannot make a single jump is not a plausible starship, and paying for a Jump-6 drive to
achieve Jump-0 is money and tonnage thrown away. The drive should be sized to what the hull can
actually fuel.

**Observed frequency**: 111 of 2000 seeded starships (5.5%) currently generate with fuel for fewer
than one full jump. In every observed case the ship carried *partial* jump fuel (for example 5 of
the 6 jump-numbers a Jump-6 drive needs), not zero.

## Clarifications

### Session 2026-07-26

- Q: Does the drive search maximize over all legal drives (which could upgrade a seed) or is it bounded above by the drive originally drawn? → A: Downgrade-only — search among drives rated no higher than the one drawn; a drawn drive that already fits is kept.
- Q: Does FR-004 (prefer the lightest drive at a given rating) apply only during a downgrade, or as a standing rule? → A: Standing rule — always normalize to the lightest drive at the installed rating, correction or not.
- Q: FR-001/FR-007/SC-001 are absolute, but the edge case where no legal drive can be fuelled permits a partial-fuel ship. Which gives? → A: Make the exception explicit — scope the requirements to "wherever any legal drive can be fuelled" and name the fallback as a permitted exception.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every generated starship can make at least one jump (Priority: P1)

A referee runs `cetools ship generate` to drop a plausible starship into their game. Whatever hull,
drives and fittings come up, the ship they get is one a crew could actually fly to another system:
its fuel tankage covers at least one complete jump at the rating its drive advertises.

**Why this priority**: This is the defect. A starship that advertises Jump-6 and can make zero jumps
is unusable at the table without the referee hand-repairing it, and it is the single most visible
symptom.

**Independent Test**: Generate ships across a large sweep of seeds and confirm that every one of
them carries jump fuel of at least (0.1 x hull tonnage x installed jump rating), counting any
FR-014 starved-hull ship separately rather than as a pass. Delivers value on its own: the generator
stops emitting broken ships.

**Acceptance Scenarios**:

1. **Given** the Overview's ship (a 100-ton hull with maneuver drive A and power plant C, leaving
   72 tons once the 10-ton bridge, the 2-ton maneuver drive, the 10-ton power plant and its 6 tons
   of fuel are deducted), **When** a ship is generated, **Then** the installed jump drive is rated
   no higher than that tonnage can fuel for one complete jump, and the ship's jump fuel covers that
   full jump. Concretely: Jump-6 via drive C would need 20 + 60 = 80 tons and does not fit, so
   Jump-4 via drive B is installed, needing 15 + 40 = 55.

   Note that 72 is the tonnage available for drive and jump fuel, not the 56 tons of *fuel tankage*
   the Overview's description reports; that 56 is 50 tons of jump fuel plus 6 of power-plant fuel.
   The two are easily confused and an earlier draft of this scenario conflated them.
2. **Given** any seed and any tabulated hull size, **When** a jump-capable ship is generated,
   **Then** its jump fuel is at least one full jump's worth at the installed rating, unless no legal
   drive for that hull could be fuelled at all (FR-014).
3. **Given** a hull with tonnage to spare, **When** a ship is generated, **Then** the jump rating is
   not lowered — a drive that can already be fuelled for a full jump keeps its rating, though its
   letter may be replaced by a lighter drive delivering that same rating.

---

### User Story 2 - The description reports an honest, non-zero jump range (Priority: P2)

A referee reads the generated prose to their players. The fuel sentence states a jump count they can
plan around ("supports the power plant for two weeks and one Jump-3 jump") instead of announcing
that the ship cannot jump.

**Why this priority**: The prose is the referee-facing product. It follows automatically from Story
1, but it is what makes the fix visible and is worth asserting separately.

**Independent Test**: Render descriptions across a seed sweep and confirm no generated starship
description contains a zero jump count, counting any FR-014 starved-hull ship separately.

**Acceptance Scenarios**:

1. **Given** any generated starship other than an FR-014 starved-hull ship, **When** its description
   is rendered, **Then** the fuel sentence reports one or more jumps at the stated rating.
2. **Given** a generated starship whose drive was downgraded, **When** its description is rendered,
   **Then** the drive letter, the stated performance rating and the jump count are mutually
   consistent.

---

### User Story 3 - Existing seeds, small craft and authored designs stay predictable (Priority: P3)

A referee who saved a seed still gets the same ship from that seed on every run, small craft output
is untouched, and a design file that deliberately specifies a short-legged ship still builds exactly
as written.

**Why this priority**: Regression safety. The change alters which jump drive a seed produces — it
lowers the rating for the ~5.5% of seeds that were broken, and substitutes a lighter equal-rated
drive wherever one exists — but it must not disturb determinism, the small-craft path, or
hand-authored designs.

**Independent Test**: Re-run seeded generation twice and compare; sweep small-craft seeds against
pre-change output; build a design file that specifies a lower jump distance than its drive rating
and confirm it still builds.

**Acceptance Scenarios**:

1. **Given** the same seed, **When** a ship is generated twice, **Then** both ships are equal.
2. **Given** any seed, **When** a small craft is generated, **Then** it is equal to the small craft
   the pre-change generator produced for that seed.
3. **Given** a caller-supplied design that explicitly requests a jump distance below one full jump,
   **When** the ship is built from it, **Then** it builds as written and is not silently altered.
4. **Given** any seed, **When** a ship is generated, **Then** the ship's name is drawn after every
   other component decision, exactly as before.

---

### Edge Cases

- **The hull cannot fuel even its lowest-rated legal jump drive.** Some hull sizes have a high
  minimum jump rating (a 100-ton hull's smallest drive is Jump-2), so a heavy power plant could in
  principle leave too little room. It does not happen with the current tables: the leanest
  combination of hull, maneuver code and power code still leaves 69 tons on a 100-ton hull, against
  the 30 that hull's cheapest fuelled drive needs, and the full cross product contains no
  counterexample. FR-014 governs anyway: the lowest-rated legal drive is installed and the ship
  carries whatever fuel fits, which is the current behaviour — the fix never makes such a ship
  worse, and the design must still fit inside its hull. This is the one case in which a generated
  starship may still report zero jumps.
- **Two legal drives share the same jump rating.** On a 400-ton hull, drives B and C both give
  Jump-1 at different tonnages. The lighter drive is chosen, since the heavier one buys nothing.
  This applies to every generated starship, not only to ships being downgraded, so it is the main
  reason a seed's output can move even when its fuel was never short.
- **Downgrading frees tonnage.** A smaller jump drive occupies fewer tons, so stepping down can make
  a rating affordable that a naive single-pass check would reject. The freed tonnage must be
  reflected in what remains for fuel and for later fittings.
- **Small craft.** Small craft mount no jump drive at all; nothing about this feature applies to
  them.
- **A design that already fits.** The overwhelming majority of seeds already carry a full jump of
  fuel. Those ships keep their jump rating, hull, maneuver drive and power plant. Their drive letter
  still normalizes to the lightest at that rating, so their freed tonnage — and therefore their
  later fittings and cargo — can shift.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every randomly generated jump-capable ship MUST carry jump fuel sufficient for at
  least one complete jump at its installed jump drive's rating for its hull, except where the
  starved-hull fallback of FR-014 applies.
- **FR-002**: When the jump drive initially selected cannot be fuelled for one complete jump, the
  generator MUST install a lower-rated jump drive rather than emit the ship with partial jump fuel —
  unless no lower-rated legal drive can be fuelled either, in which case FR-014 governs.
- **FR-003**: The installed jump drive MUST be the highest-rated drive, among those legal for the
  hull and rated no higher than the drive originally selected, whose own tonnage plus one complete
  jump of fuel fits within the tonnage left once the mandatory systems (bridge, maneuver drive,
  power plant and power-plant fuel) have been deducted from the hull's tonnage. The adjustment never
  raises a ship's jump rating above what the random selection produced.
- **FR-004**: Where two or more legal drives yield the same jump rating for a hull, the one
  occupying the least tonnage MUST be installed. This is a standing rule, applied to every generated
  starship — not only to ships whose drive is downgraded. It preserves the ship's jump rating and
  consumes no draw. It does still free tonnage, which flows on per FR-005 and can therefore change
  the ship's later fittings and cargo.
- **FR-005**: Tonnage freed by installing a lighter jump drive — whether through a downgrade
  (FR-003) or a same-rating substitution (FR-004) — MUST become available to the ship's subsequent
  allocations (jump fuel first, then discretionary fittings and cargo). Those subsequent allocations
  keep the generator's existing order and existing affordability rules; this feature changes what
  tonnage they are handed, not how they spend it.
- **FR-006**: A generated ship whose originally selected jump drive can already be fuelled for one
  complete jump MUST retain that drive's jump rating. Its drive letter MAY still be replaced by a
  lighter drive of the same rating under FR-004, with the freed tonnage flowing on per FR-005.
- **FR-007**: A generated starship's description MUST NOT report a jump count of zero, except where
  the starved-hull fallback of FR-014 applies. In that excepted case the description MUST still be
  internally consistent: the drive letter, the stated performance rating and the reported jump count
  agree with one another and with the drive actually installed.
- **FR-008**: The jump-drive adjustment MUST NOT itself consume a random draw. It is decided from
  the hull, the drive already drawn and the tonnage budget. The jump, maneuver and power codes MUST
  continue to be drawn in their existing order, and the ship name MUST remain the last draw of every
  path.

  This does **not** promise that a seed's total draw count is unchanged. Freed tonnage (FR-005)
  feeds the affordability checks of later selections, and some of those selections draw
  conditionally on what they can afford, so a seed whose drive changes may legitimately consume a
  different number of draws further down. FR-008 constrains the adjustment step; it does not
  constrain the downstream consequences of installing a smaller drive.
- **FR-009**: Within a given release, the same seed MUST produce the same ship on every run.
  Seed-to-ship stability *across* releases is not promised, and is deliberately broken by this
  feature for roughly half of all seeds (see Assumptions).
- **FR-010**: Small-craft generation MUST be unaffected.
- **FR-011**: Generation constrained to a specific hull size MUST continue to honour that hull size;
  the adjustment changes the drive, never the hull.
- **FR-012**: A ship built from a caller-supplied design MUST NOT be adjusted, whether that design
  was loaded from a file or constructed in memory. A deliberately short-legged design remains
  buildable as written. The correction is generation policy: it applies only where cetools is
  choosing components on the caller's behalf, and to no other entry point.
- **FR-013**: Every generated ship MUST remain rules-legal and within its hull tonnage after the
  adjustment. "Rules-legal" means the design passes exactly the same validation a caller-supplied
  design must pass. Generation adds no separate standard and relaxes none.
- **FR-014**: **Starved-hull fallback.** Where no drive legal for the hull can be fuelled for one
  complete jump within the tonnage remaining after the mandatory systems, the lowest-rated legal
  drive MUST be installed and the ship MUST carry whatever jump fuel fits. Where several legal
  drives share that lowest rating, FR-004 still governs the choice among them, so the lightest is
  installed. This covers the degenerate case in which the mandatory systems leave no tonnage at all
  for a jump drive. Such a ship is the sole permitted exception to FR-001, FR-007, SC-001, SC-002
  and SC-004, and MUST still satisfy FR-013.

  A ship is an FR-014 ship exactly when its jump fuel falls short of one complete jump at its
  installed rating **and** no drive legal for its hull could have been fuelled for one complete jump
  within its own tonnage budget. Both halves are recomputable from the finished ship (its hull,
  bridge, maneuver drive and power plant), so the classification SC-001 depends on is observable
  rather than internal.

  The case is unreachable with the current tables: no combination of hull, maneuver code and power
  code starves a hull, verified over the full cross product rather than sampled. It is specified so
  the rule has a defined boundary rather than an undefined one.

### Key Entities

- **Jump drive option**: A drive letter legal for a given hull, carrying a tonnage cost and a jump
  rating that depends on the hull size. A letter is legal for a hull exactly when the drive
  performance table gives that letter a rating at that hull size; every tabulated hull has at least
  one legal drive, the smallest having three. Several letters can share a rating on large hulls, but
  no two letters share a tonnage cost, so FR-004's "lightest at a rating" always names exactly one
  drive.
- **Jump fuel**: Tonnage set aside for jumping, priced at one tenth of the hull tonnage per jump
  number. One complete jump at rating N costs 0.1 x hull x N.
- **Mandatory systems**: Bridge, maneuver drive, power plant and power-plant fuel — allocated before
  any discretionary fitting and therefore the baseline against which drive affordability is judged.
- **Generated ship**: The finished design, whose stated performance rating and stated jump count
  must agree.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across a sweep of at least 2000 seeds, zero generated starships report fewer than one
  jump at their stated rating — down from 111 of 2000 (5.5%) today. The sweep MUST separately count
  ships that hit the FR-014 starved-hull fallback; that count is expected to be zero, and any
  non-zero result is reported rather than silently absorbed.
- **SC-002**: Across the same sweep, every generated starship's jump fuel is at least one tenth of
  its hull tonnage multiplied by its installed jump rating, excepting FR-014 ships. This is SC-001
  stated as arithmetic on the finished ship rather than as a count of failures; the two identify the
  same population, and SC-004 identifies it a third time through the rendered prose. They are kept
  separate because they are checked at three different layers — the fuel figure, the sweep tally and
  the referee-facing sentence — and a fix that satisfied only one of them would not be a fix.
- **SC-003**: Across the same sweep, every generated ship's total allocated tonnage remains within
  its hull tonnage.
- **SC-004**: Across the same sweep, no generated starship description contains a zero jump count,
  excepting FR-014 ships.
- **SC-005**: For every seed in the sweep, small-craft generation yields a ship equal to the one the
  pre-change generator yields for that seed.
- **SC-006**: Across the same sweep, generating from a fixed seed twice yields equal ships in 100%
  of seeds, on the standard-hull path, the small-craft path and the hull-constrained path alike.
- **SC-007**: Across the same sweep, every generated starship that could already be fuelled for a
  full jump retains its pre-change jump rating, hull tonnage, maneuver drive and power plant. Where
  its drive letter changes, the substituted drive occupies strictly less tonnage and delivers the
  same jump rating. "Pre-change" means the ship this repository's generator produced for that seed
  immediately before this feature, obtained by running that generator over the sweep. It does not
  mean the pinned baseline of an earlier feature, which this feature legitimately invalidates.
- **SC-008**: Across the same sweep, on both the standard-hull and small-craft paths, the ship name
  is the final draw of every generation and is drawn exactly once, and the jump, maneuver and power
  codes are drawn in that order. This is the measurable form of FR-008; note that per FR-008 the
  total draw count per seed is *not* expected to be stable across this feature.
- **SC-009**: Across the same sweep, every ship generated with a hull size specified has that hull
  size.
- **SC-010**: Every design in the repository's authored example designs builds to a ship equal to
  the one it built before this feature, including any design whose stated jump distance is below one
  full jump at its drive's rating.

### Requirement Coverage

Every functional requirement has at least one acceptance scenario or success criterion that fails if
the requirement is violated.

| Requirement | Covered by |
| --- | --- |
| FR-001 one full jump of fuel | US1 AS2, SC-001, SC-002 |
| FR-002 downgrade rather than under-fuel | US1 AS1, SC-001 |
| FR-003 highest affordable rating at or below the drawn one | US1 AS1, SC-002, SC-007 |
| FR-004 lightest drive at a rating, always | US1 AS3, SC-007 |
| FR-005 freed tonnage flows on | SC-002, SC-003 |
| FR-006 an affordable rating is kept | US1 AS3, SC-007 |
| FR-007 no zero jump count in prose | US2 AS1, US2 AS2, SC-004 |
| FR-008 the adjustment draws nothing | US3 AS4, SC-008 |
| FR-009 seeds reproduce within a release | US3 AS1, SC-006 |
| FR-010 small craft untouched | US3 AS2, SC-005 |
| FR-011 hull size honoured | SC-009 |
| FR-012 caller-supplied designs untouched | US3 AS3, SC-010 |
| FR-013 rules-legal, inside the hull | SC-003 for the tonnage half; the validation half holds by construction, since generation returns its design through the same build path a caller-supplied design takes, and a sweep that completes has exercised it |
| FR-014 starved-hull fallback | SC-001 (counted separately, expected zero) |

## Assumptions

- **"Equal ships"** means every field of the finished ship compares equal, which is the comparison
  SC-005, SC-006 and SC-010 use. It is a stronger claim than the rendered prose matching and a
  weaker one than the serialized file matching byte for byte; where earlier features said
  "byte-for-byte", this feature means field equality.
- "Supports one jump" means the ship's jump fuel covers one complete jump at the rating its
  installed drive delivers for its hull — the same arithmetic the description already uses to report
  its jump count. Fuel beyond one jump is welcome but not required.
- The affordability test FR-003 states (drive tonnage plus one jump of fuel fits the budget) and the
  arithmetic the generator already uses to decide how many jumps its remaining tonnage buys must
  agree at the boundary, or the search could select a rating the later arithmetic then refuses to
  fund. They do agree for every hull and rating in the current tables, but the agreement rests on
  floating-point behaviour rather than on anything the rules guarantee, so it is treated as a
  property to pin, not one to assume.
- Nothing in this feature constrains the ship's cost in credits. The Overview cites wasted money as
  motivation, but cost follows from the components chosen: a lighter drive costs less, and no
  requirement puts a floor or ceiling on the result.
- The correction adjusts only the jump drive. The hull, maneuver drive and power plant selections
  produced by the random draws are left alone, matching the reported expectation that the ship "be
  built with a lower rated jump drive". Power-plant fuel follows from the power plant alone, so it
  is unchanged too.
- The power plant stays legal in both correction cases. Its legal candidate set is bounded below by
  the higher of the jump and maneuver ratings, so an FR-004 same-rating substitution leaves that
  floor untouched, and an FR-003 downgrade only lowers it. A drive change can therefore never
  invalidate a power plant already drawn, and the power plant is deliberately not re-drawn.
- When two drives share a rating, the lighter is strictly better for the ship, so preferring it needs
  no random choice and consumes no draw. This preference is applied to every generated starship, so
  far more seeds change output than the 5.5% that were actually broken: roughly 54% of seeds move,
  since the lightest-drive rule reaches every ship whose drawn letter was not already the lightest at
  its rating. Stability of output against the pre-change generator is therefore not a goal of this
  feature, and SC-007 rather than a whole-ship comparison is what guards against regression.
- Where no legal drive can be fuelled for a full jump, the lowest-rated legal drive is installed and
  the ship carries whatever fuel fits. This is never worse than today's behaviour. It is specified
  as FR-014 and is a permitted exception to the one-jump-minimum rule, not a silent gap in it. The
  case does not arise with the current tables: it is absent from the full cross product of hull,
  maneuver code and power code, which is a stronger result than the 2000-seed sample that first
  suggested it, and the smallest budget any combination can leave is comfortably more than the
  cheapest fuelled drive on that hull.
- The feature is limited to random generation. Building a ship from a caller-supplied design is a
  deliberate act by the author and is out of scope.
- The stored design schema does not change, so a design saved by the pre-change generator, including
  one carrying an over-rated drive and partial jump fuel, still loads and still builds to the same
  ship. This feature changes which drive the generator writes, never what a stored design means.
- The existing pinned baseline of pre-feature generated designs (captured for the ship-names feature
  to prove that naming inserted no draws) will no longer match for any starship entry whose jump
  drive was over-rated or whose rating is available from a lighter drive, which is far more than the
  3 of its 50 starship entries the downgrade alone would have moved. That guard's intent, that no
  extra draw appears before the name, is preserved by restating it directly as SC-008 rather than by
  re-pinning ship data, because per FR-008 the data legitimately moves while the invariant does not.
