from __future__ import annotations

from cetools.engine.rolls import RollName, Rolls

# The ageing ladder, worst first. The roll is 2D6 - terms_served; each rung lists
# the characteristics it reduces and by how much. Anything of 1 or more is unhurt.
#
# The last rung is unreachable in a normal career: 2D6 bottoms out at 2 and the
# term cap is 7, so the worst ordinary roll is 2 - 7 = -5. Only a natural 12 on
# re-enlistment, which forces an eighth term, reaches -6.
_LADDER: dict[int, tuple[tuple[str, int], ...]] = {
    0: (("Strength", 1),),
    -1: (("Strength", 1), ("Dexterity", 1)),
    -2: (("Strength", 1), ("Dexterity", 1), ("Endurance", 1)),
    -3: (("Strength", 2), ("Dexterity", 1), ("Endurance", 1)),
    -4: (("Strength", 2), ("Dexterity", 2), ("Endurance", 1)),
    -5: (("Strength", 2), ("Dexterity", 2), ("Endurance", 2)),
}

_WORST = (("Strength", 2), ("Dexterity", 2), ("Endurance", 2), ("Intelligence", 1))

AGING_STARTS_AT_AGE = 34


def apply_aging(
    characteristics: dict[str, int], terms_served: int, rolls: Rolls
) -> dict[str, int]:
    """The characteristics after ageing. Unchanged when the roll comes up 1 or more."""
    roll = rolls.two_d6(RollName.AGING) - terms_served
    if roll >= 1:
        return dict(characteristics)

    reductions = _LADDER.get(roll, _WORST)
    aged = dict(characteristics)
    for stat, amount in reductions:
        aged[stat] = max(0, aged[stat] - amount)
    return aged
