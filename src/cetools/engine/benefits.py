from __future__ import annotations

from dataclasses import dataclass

from cetools.engine.careers.base import Career
from cetools.engine.models import (
    Benefit,
    Cash,
    Item,
    Shares,
    apply_stat_boost,
    parse_stat_boost,
)
from cetools.engine.rolls import RollName, Rolls

# Extra benefit rolls granted by rank on leaving a career.
RANK_BONUS_ROLLS = {4: 1, 5: 2, 6: 3}

MAX_CASH_ROLLS = 3
MATERIAL_DM_MINIMUM_RANK = 5

# Benefits a career can grant at most once. A repeat is rerolled.
ONCE_ONLY = frozenset({"Explorers' Society", "Research Vessel", "Courier Vessel"})

SHIP_SHARES = "1D6 Ship Shares"

_MAX_REROLLS = 100


@dataclass(frozen=True)
class MusterOut:
    """What a character leaves a career with.

    `skills` is absent on purpose: a material benefit never grants a skill. Skills
    are read on the way in, for the Gambling cash DM, and never written.
    """

    benefits: list[Benefit]
    characteristics: dict[str, int]


def roll_material_benefit(
    career: Career,
    material_dm: int,
    rolls: Rolls,
    granted: set[str],
) -> str:
    """A material benefit, rerolling any once-only benefit already granted."""
    last = len(career.material_benefits) - 1
    for _ in range(_MAX_REROLLS):
        idx = max(0, min(last, rolls.d6(RollName.MATERIAL_BENEFIT) + material_dm - 1))
        name = career.material_benefits[idx]
        if name in ONCE_ONLY and name in granted:
            continue
        return name

    # A degenerate script (e.g. a ScriptedRolls fixed on one value) that keeps
    # landing on an already-granted once-only benefit would otherwise loop
    # forever. Fall back to the first entry that is not one—every real career
    # table has one.
    for name in career.material_benefits:
        if not (name in ONCE_ONLY and name in granted):
            return name
    raise RuntimeError(
        f"Career '{career.name}' has no material benefit outside the"
        f" already-granted once-only set {sorted(ONCE_ONLY & granted)}"
    )


def muster_out(
    career: Career,
    terms_served: int,
    rank: int,
    skills: dict[str, int],
    characteristics: dict[str, int],
    rolls: Rolls,
) -> MusterOut:
    """The benefits drawn on leaving a career.

    One roll per term served, plus a rank bonus. The first three are cash; the
    rest are material. Gambling gives +1 on cash rolls, and rank 5+ gives +1 on
    material rolls, which is what puts the last row of the table in reach.
    """
    total_rolls = terms_served + RANK_BONUS_ROLLS.get(rank, 0)
    cash_dm = 1 if skills.get("Gambling", -1) >= 0 else 0
    material_dm = 1 if rank >= MATERIAL_DM_MINIMUM_RANK else 0

    benefits: list[Benefit] = []
    granted: set[str] = set()
    cash_rolls_used = 0

    for _ in range(total_rolls):
        if cash_rolls_used < MAX_CASH_ROLLS:
            idx = max(0, min(6, rolls.d6(RollName.CASH_BENEFIT) + cash_dm - 1))
            benefits.append(Cash(amount=career.cash_benefits[idx]))
            cash_rolls_used += 1
            continue

        entry = roll_material_benefit(career, material_dm, rolls, granted)
        granted.add(entry)

        # This is the one place a material table entry stops being a string.
        if entry == SHIP_SHARES:
            benefits.append(Shares(quantity=rolls.d6(RollName.SHIP_SHARES)))
            continue

        boost = parse_stat_boost(entry)
        if boost is not None:
            characteristics = apply_stat_boost(characteristics, boost)
            benefits.append(boost)
            continue

        benefits.append(Item(name=entry))

    return MusterOut(benefits=benefits, characteristics=dict(characteristics))
