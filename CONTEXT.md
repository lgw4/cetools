# cetools

Cepheus Engine character, world and ship generation tools. This glossary fixes the
vocabulary the code and its documentation use; it is not a spec and holds no
implementation detail.

## Language

### Chance

**Roll**:
One random decision the rules make, named by its intent rather than its position in a
die sequence. Every roll the engine can make is enumerated in one place.
_Avoid_: die roll, dice, RNG call

**Rolls seam**:
The single interface through which the engine reaches chance, with a production adapter
backed by real dice and a test adapter that answers rolls by name.
_Avoid_: dice service, randomizer, RNG provider

### Ship design

**Design**:
The declarative build order for a ship — what to fit, stated as data. Mirrors the TOML
schema and is legal in *shape* without necessarily being legal by the *rules*.
_Avoid_: blueprint, plan, spec, config

**Ship**:
The computed result of building a design: costed, crewed, validated, and carrying the
design it came from.
_Avoid_: vessel, craft, hull

**Build**:
Turning a design into a ship, allocating every component in SRD order and rejecting
anything the rules forbid. The sole authority on rules legality.
_Avoid_: validate, compile, assemble

**Hull class**:
Which ruleset a hull builds under — starship or small craft. Governs bridge versus
cockpit, whether a jump drive is permitted, and whether bays are available.
_Avoid_: ship type, size class, category

**Rating**:
A drive's delivered performance on a given hull, as a referee states it: Jump-2, 4-G.
Distinct from the drive **code** that produces it, since the mapping depends on hull
tonnage and several codes can deliver the same rating.
_Avoid_: level, grade, performance

**Code**:
The SRD letter identifying a drive, as stored in a design. Small-craft codes carry an
`s` prefix.
_Avoid_: drive letter, drive type, class

### Constrained generation

**Pinned value**:
A value a referee supplied. A promise: honoured, or reported as an unmet constraint.
_Avoid_: fixed value, locked value, override, requirement

**Rolled value**:
A value the referee left unspecified, drawn from chance. A preference: silently declined
if it does not fit the tonnage budget.
_Avoid_: random value, default, generated value

**Pinned absence**:
A referee's answer that an optional component is *not* to be fitted. A pinned value like
any other, and a different answer from leaving the field unspecified: one guarantees no
armour, the other rolls for it.
_Avoid_: null, empty, off, disabled

**Unmet constraint**:
A pinned value the tonnage budget could not accommodate, recorded with what was asked,
what was got, and why.
_Avoid_: failure, error, violation, warning

**Curated list**:
A hand-picked subset of an SRD table that keeps *rolled* output plausible. Never bounds
what may be pinned.
_Avoid_: allowed values, whitelist, options
