from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    """Which rules a character is generated under.

    cetools departs from the SRD in two places, both settled in
    `specs/002-scout-career-character/spec.md`. They travel together as a policy
    rather than as loose flags, so the two nonsense combinations cannot be asked
    for.
    """

    reroll_until_qualified: bool
    """How a character gets into the career they asked for.

    True: reroll the whole set of characteristics until the qualification
    characteristic meets the career's target as a raw number — no dice check, and
    enlistment can never fail. False: roll characteristics once, then make the
    SRD's `2D6 + DM >= target` enlistment check, which can fail.
    """

    natural_12_forces_extra_term: bool
    """What a natural 12 on re-enlistment means at the 7-term cap.

    True (SRD): the character cannot leave and serves an eighth term.
    False: the 7-term cap is hard and muster-out begins instead.
    """


HOUSE = Rules(reroll_until_qualified=True, natural_12_forces_extra_term=False)
"""cetools' own rules, and the default: you get the career you asked for, and
seven terms is the end of it."""

SRD = Rules(reroll_until_qualified=False, natural_12_forces_extra_term=True)
"""The Cepheus Engine SRD as written: enlistment is a check you can fail, and a
natural 12 keeps you in for an eighth term."""
