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

Two failure classes exist and are handled in different places. Whether a pinned value is
*legal* — armour at a multiple of 5%, no jump drive on a small craft — is knowable
immediately, so it is rejected at the point of input. Whether it is *affordable* depends
on a tonnage budget that is not settled until fuel is computed, which is not until every
other component is chosen, so it is only knowable at assembly. Attempts to validate
affordability earlier will not work.

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
