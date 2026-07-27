# Constrained ship generation: pinned values are promises, rolled values are preferences

The ship generator was all-or-nothing — a referee who needed a specific ship had to
either roll repeatedly or abandon generation for a hand-authored TOML design. We added
constrained generation, in which a referee pins some values and the generator rolls the
rest, and we resolved the resulting conflicts with one rule: **a pinned value is a
promise, a rolled value is a preference.** A rolled value that will not fit is silently
declined, exactly as before; a pinned value that will not fit is still declined, but is
recorded as an unmet constraint and reported. Generation therefore never fails on
tonnage, which is why `generate_ship` now returns a `GenerationResult` carrying both the
ship and the constraints it could not meet, rather than a bare `Ship`.

## Consequences

The generator loses its *legal by construction* framing at the interface, though not in
fact. It still never emits an illegal ship, but it can now emit a ship that is not the
one that was asked for, so callers must read `unmet` to know whether they got what they
requested. This is the price of never failing.

Three outcomes exist at assembly, not two. A pinned value may be *met*; *unmet*, meaning
the tonnage budget could not accommodate it, which degrades and warns but still yields a
ship; or *illegal*, meaning `build_ship` rejects it outright, which yields no ship at
all. Only the middle case is a degradation.

Validation is correspondingly split, but not along the line one would first guess.
Whether a pinned value is *affordable* depends on a tonnage budget that is not settled
until fuel is computed, which is not until every other component is chosen, so it is
only ever knowable at assembly. Whether it is *legal* is knowable at the point of input
**only as far as the tables and the component-fit records know** — an unknown fitting
name, a weapon that does not exist, a drive rating not tabulated for the chosen hull, a
jump drive on a small craft. Rules that live inside `build_ship` — armour at a multiple
of 5% is the clearest example — are deliberately not duplicated outward to make them
catchable earlier, because the shape-versus-rules boundary those modules document is
worth more than earlier feedback. Such violations surface at assembly and re-enter the
same revise loop that unmet constraints use, so the referee never loses the session; the
feedback simply arrives later for that narrow class.

Pinning a value consumes no dice. This matches how `hull_size` has always behaved and
keeps the unconstrained draw sequence byte-identical, so `tests/data/baseline/designs.json`
holds. The cost is that two runs sharing a seed but differing in one pin diverge
completely downstream of that pin; the alternative — drawing and discarding to keep the
stream aligned — was rejected as a subtle rule to hold in mind for a property nobody had
asked for.

## Rejected alternatives

**Ratings, not drive codes.** A referee pins *Jump-2*, not *drive C*, and the rating is
resolved to the lightest code delivering it on the chosen hull. Storing codes would have
matched `ShipDesign` and the TOML schema exactly and needed no translation, but the
mapping is hull-dependent and a referee does not think in letters. The
lightest-code-at-a-rating rule is not new: `_fit_jump_drive` already applies it so that
tonnage freed by a downgrade flows on to fuel and fittings.

**The full SRD tables, not the curated policy lists.** `_ARMOR_CHOICES`,
`_COMPUTER_PROFILES` and `_FITTING_CHOICES` exist to keep *random* output plausible, not
to bound what a referee may ask for. A pinned value is therefore validated against the
SRD tables and `build_ship`, so bonded superdense armour or a vault can be pinned even
though the generator would never roll either. Restricting pins to the curated lists
would have allowed a closed numbered menu at each prompt and made every constrained ship
reachable by chance, at the cost of sending any referee with an unusual requirement back
to hand-authored TOML.
