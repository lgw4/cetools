# cetools

Generators and design tools for the Cepheus Engine SRD: characters, worlds and
ships. This glossary fixes the vocabulary those tools share, so that a term means
one thing in the tables, the engine, the prompts and the prose.

Spelling throughout the project is American English—`armor`, `maneuver`,
`catalog`—in documentation and comments as much as in identifiers.

## Language

**Armor layer**:
One entry in a design's armor: a material and a percent of hull tonnage. A ship
may carry several.
_Avoid_: armor option

**Armor option**:
A coating applied to the hull as a whole: reflec, self-sealing, stealth. Priced
per ton of hull and added at most once per ship, never per layer.
_Avoid_: armor extra, armor upgrade

**Accommodation**:
The tonnage a component obliges the ship to spend housing the crew it requires.
A drive obliges its engineers' accommodation; a turret obliges its gunner's.
_Avoid_: quarters, berthing

**Stateroom**:
The SRD component that provides accommodation. One per crew member.

**Berth**:
One place aboard where a crew member can sleep: a stateroom, or a seat in a
small craft's cockpit. *Accommodation* is the tonnage; a berth is what that
tonnage buys. A design may carry fewer berths than crew, and the description
says so; nothing refuses it, since the SRD never requires one per head.
_Avoid_: bunk, bed, berthing

**Coherent**:
A ship that is internally consistent: its crew have berths, and nothing is paid
for twice. Distinct from *optimal*, which cetools does not attempt: optimality
would require a purpose to optimize for, and cetools never invents one.
_Avoid_: optimal, valid

**Hull class**:
Which ruleset a hull builds under: starship or small craft. It governs what a
design may carry at all, not merely what it can afford.

**Pin**:
To fix a component's value, so generation does not roll it.

**Absent**:
A pinned *absence*: the answer "no armor", as opposed to leaving armor to the
dice. Distinct from an unanswered question, which rolls.

**Purpose**:
The clause completing "the <name> is ..." in a description's first sentence.
Author-supplied; cetools never generates one.

**Unmet constraint**:
A pinned value the tonnage budget could not accommodate, reported alongside the
ship rather than replacing it. A *rolled* value that will not fit is declined
silently: it was a preference, not a promise.
