# 1. Accommodation is part of a component's cost

Date: 2026-08-03

Status: accepted

## Context

Generated ships routinely carried more crew than berths. A 1,200-ton starship
came out with a crew of ten and no staterooms; a 400-ton ship with a crew of
nine, no staterooms and no cargo. Across the first 500 seeds, 493 starships and
465 small craft were short, the worst of them by sixteen.

The cause was that staterooms and crew were decided independently and never
reconciled. Staterooms were drawn from a die roll that consulted nothing. Crew
was derived afterwards from the ship that had been built: engineers scale with
drive tonnage, gunners with the weapons mounted, screen operators with the
screens fitted. Nothing compared the two.

cetools already assumed one stateroom per crew member — the description's
passenger arithmetic subtracted the whole crew from the stateroom count to work
out spare capacity. When staterooms fell short the subtraction went negative and
was clamped to zero, so the description reported "the ship cannot carry any
additional passengers": a sentence that reads like a design choice and conceals
ten people with nowhere to sleep.

## Decision

**Accommodation is part of what a component costs.** Every component that
obliges a crew member reserves that crew member's berth as part of its own
affordability test, and the reservation is spent from the same tonnage ledger
the component's own tonnage is spent from.

This is not a new idea in the generator; it is the existing one applied
consistently. A weapon bay's affordability has always included the fire control
the bay obliges the ship to carry. Accommodation is the same kind of obligation.

Concretely:

- `TonnageLedger.affords(tons, crew)` and `.spend(tons, crew)` take a crew count
  beside their tonnage, and `.accommodate(crew)` berths crew that no component
  can decline (the pilot, the navigator, the engineers).
- The pilot's and navigator's berths are reserved before anything is chosen.
  A design whose computer carries jump-control software needs no navigator, so
  the computer is now drawn before the drives — it costs no tonnage, and drawing
  it first is what makes the reservation exact rather than conservative.
- Turrets, bays and screens each cost a berth alongside their own tonnage.
- The staterooms are selected **last** on both paths, after every component that
  can add crew, and start from the berths the ledger already holds.
- `engineers_for` and `command_crew` are public in `builder.py` and are the sole
  authority on those two derivations, so generation counts crew the way the
  builder does. Two copies that drift would break the guarantee in silence.

**Coherence is achieved by narrowing candidates, never by retracting a choice.**
Generation remains a single forward pass. Retraction would make generation a
search, and a search would need an objective, which would need a purpose, which
cetools does not invent.

**Two consequences that were not obvious in advance:**

*A small craft's cockpit is accommodation.* The SRD's Small Craft Cockpit table
carries a Crew column — a 1-man cockpit seats one crew, a 2-man seats two — and
the crew who sit in it need no stateroom. `CockpitRow` previously omitted that
column on the reasoning that the SRD "never reconciles cockpit capacity with the
crew calculation", and that reasoning is preserved for what it was about:
nothing caps a craft's minimum crew against its seats. But reading the table the
other way — every crew member needs a stateroom, and a cockpit provides none —
makes the SRD's own sample small craft illegal and puts every hull from 10 to 20
tons beyond housing its own crew. Cockpit seats count as berths; they are not
passenger space, since only the larger control cabins (out of scope here) carry
a passenger.

*The starship drive path did not need the filter the spec proposed.* Issue #60
called an affordability filter on the starship maneuver and power draws "the
largest single piece of the change and the source of most of its effect". It was
written, and then measured: it rejected **none** of 5,390 legal drive
combinations across all eighteen starship hulls, with or without a navigator. A
maneuver drive and a power plant that fit an SRD starship hull at all leave room
for the engineers they oblige. The filter was removed rather than kept as
decoration. What actually delivers the effect on this path is `_fit_jump_drive`,
which does weigh the berths when choosing a rating, and the order in
`generate_ship`, which berths the engineers before it buys a drop of jump fuel.

The small-craft equivalent *is* load-bearing, and is kept: that budget is tight
enough that dropping any part of it changes what is generated.

## Consequences

- **This change alters what a seed produces.** `tests/data/baseline/designs.json`
  was regenerated: all 100 pinned designs moved. Seed 42's 400-ton ship went
  from nine crew and no staterooms to nine crew, nine staterooms and 141 tons of
  cargo.
- **Two pre-change regression nets were narrowed to the hull.**
  `test_sc005` and `test_sc007` pinned whole seeded designs against
  `pre_change_sweep.json` on the claim that the *jump-fuel* feature moved
  nothing it should not have. Accommodation moves those values deliberately, so
  what survives is the assertion that the hull a seed draws is untouched — the
  hull is still the first draw, so no later filter can reach back and change it.
  Their replacement is the invariant sweep, which asserts a property rather than
  a snapshot and is the stronger net.
- **One hull cannot be housed.** A 10-ton small craft has 1.2 tons free once its
  lightest legal drives and cockpit are in; a berth costs 4. It is generated with
  the shortfall reported rather than refused, and the arithmetic is pinned by
  `test_no_ten_ton_hull_can_berth_its_crew_however_it_is_fitted` so the exception
  cannot become a hiding place for a defect.
- **The SRD's own worked free trader now reports a shortfall.** The Beowulf
  carries four staterooms against five crew and two middle passengers. Under one
  berth per person it is a room short. The shortfall was always there — the
  passenger sentence has always said it "cannot carry any additional passengers"
  while its design file declares two — and only the silence about it is new.
- **`build_ship` still accepts a short-crewed design.** The SRD states that a
  stateroom holds one or two people and that its tonnage includes life support,
  but never that every crew member must have one. Refusing would invent a rule
  and would block a referee from iterating on a design.
- **A pinned stateroom count caps the berths reserved.** That is what keeps a
  deliberate zero a different answer from an unanswered question: the ship is
  built exactly as it would have been before accommodation was reserved, and the
  description reports who has nowhere to sleep.

## Alternatives considered

**Post-hoc correction** — build the ship, then add staterooms for any crew left
over. Rejected: the tonnage has already been spent, so correction means either
overrunning the hull or taking something back out, and taking something back out
is retraction under another name. It also produces a ship the referee reads
after it has been revised, rather than the ship that was chosen.

**Backtracking** — choose, detect the shortfall, and re-choose. Rejected for the
reason above: it makes generation a search, and a search needs an objective
cetools has no way to supply.

**Double-occupancy berths** — two crew per stateroom, which the SRD permits.
Rejected for the reservation: the SRD's baseline is one person per stateroom and
offers two as a passenger arrangement, and a berth at half price would barely
constrain the choices this change exists to constrain. It was also rejected for
the *report*, where it would have kept the Beowulf quiet, because the
description's passenger arithmetic has always counted one room per crew member
and two thresholds in one paragraph would contradict each other.

**Exempting small craft** — leaving the guarantee to starships. Rejected: a
referee should not have to remember which ruleset the guarantee covers. Reading
the cockpit's crew column made it reachable on every hull but one.
