from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cetools.engine.models import MishapOutcome
from cetools.engine.rolls import RollName, Rolls

_PHYSICAL_STATS = ("Strength", "Dexterity", "Endurance")


@dataclass(frozen=True)
class InjuryEntry:
    candidate_stats: tuple[str, ...]
    primary_dice: int
    primary_fixed: int
    secondary_amount: int


@dataclass(frozen=True)
class MishapEntry:
    discharge_type: Literal["honorable", "dishonorable", "medical", "none"]
    imprisoned: bool
    debt: int
    injury_rolls: int


INJURY_TABLE: tuple[InjuryEntry, ...] = (
    InjuryEntry(
        candidate_stats=_PHYSICAL_STATS, primary_dice=1, primary_fixed=0, secondary_amount=2
    ),
    InjuryEntry(
        candidate_stats=_PHYSICAL_STATS, primary_dice=1, primary_fixed=0, secondary_amount=0
    ),
    InjuryEntry(
        candidate_stats=("Strength", "Dexterity"),
        primary_dice=0,
        primary_fixed=2,
        secondary_amount=0,
    ),
    InjuryEntry(
        candidate_stats=_PHYSICAL_STATS, primary_dice=0, primary_fixed=2, secondary_amount=0
    ),
    InjuryEntry(
        candidate_stats=_PHYSICAL_STATS, primary_dice=0, primary_fixed=1, secondary_amount=0
    ),
    InjuryEntry(candidate_stats=(), primary_dice=0, primary_fixed=0, secondary_amount=0),
)
if len(INJURY_TABLE) != 6:
    raise ValueError(f"INJURY_TABLE must have exactly 6 entries, got {len(INJURY_TABLE)}")

SURVIVAL_MISHAPS_TABLE: tuple[MishapEntry, ...] = (
    MishapEntry(discharge_type="none", imprisoned=False, debt=0, injury_rolls=2),
    MishapEntry(discharge_type="honorable", imprisoned=False, debt=0, injury_rolls=0),
    MishapEntry(discharge_type="honorable", imprisoned=False, debt=10_000, injury_rolls=0),
    MishapEntry(discharge_type="dishonorable", imprisoned=False, debt=0, injury_rolls=0),
    MishapEntry(discharge_type="dishonorable", imprisoned=True, debt=0, injury_rolls=0),
    MishapEntry(discharge_type="medical", imprisoned=False, debt=0, injury_rolls=1),
)
if len(SURVIVAL_MISHAPS_TABLE) != 6:
    raise ValueError(
        f"SURVIVAL_MISHAPS_TABLE must have exactly 6 entries, got {len(SURVIVAL_MISHAPS_TABLE)}"
    )


def _apply_injury(
    entry: InjuryEntry, characteristics: dict[str, int], rolls: Rolls
) -> tuple[dict[str, int], dict[str, int]]:
    """The injured characteristics, and what each reduction was."""
    if not entry.candidate_stats:
        return dict(characteristics), {}

    if len(entry.candidate_stats) > 1:
        primary_stat = rolls.choose(entry.candidate_stats, RollName.INJURY_STAT)
    else:
        primary_stat = entry.candidate_stats[0]

    amount = rolls.d6(RollName.INJURY_AMOUNT) if entry.primary_dice > 0 else entry.primary_fixed
    reductions = {primary_stat: amount}

    injured = dict(characteristics)
    injured[primary_stat] = max(0, injured[primary_stat] - amount)

    if entry.secondary_amount > 0:
        for stat in _PHYSICAL_STATS:
            if stat == primary_stat:
                continue
            reductions[stat] = entry.secondary_amount
            injured[stat] = max(0, injured[stat] - entry.secondary_amount)

    return injured, reductions


@dataclass(frozen=True)
class Mishap:
    """What ended the career, and what it cost."""

    outcome: MishapOutcome
    debt: int
    characteristics: dict[str, int]


def resolve_survival_mishap(rolls: Rolls, characteristics: dict[str, int]) -> Mishap:
    """Roll on the Survival Mishaps table. Returns the injured character; mutates nothing."""
    mishap_roll = rolls.d6(RollName.MISHAP)
    entry = SURVIVAL_MISHAPS_TABLE[mishap_roll - 1]

    injured = dict(characteristics)
    injury_reductions: dict[str, int] = {}
    zeroed_stats: list[str] = []

    if entry.injury_rolls > 0:
        if entry.injury_rolls == 1:
            injury_roll = rolls.d6(RollName.INJURY)
        else:
            injury_roll = min(rolls.d6(RollName.INJURY), rolls.d6(RollName.INJURY))
        injured, injury_reductions = _apply_injury(
            INJURY_TABLE[injury_roll - 1], characteristics, rolls
        )
        zeroed_stats = [
            stat for stat in injury_reductions if characteristics[stat] > 0 and injured[stat] <= 0
        ]

    injury_crisis = False
    debt = 0
    if zeroed_stats:
        injury_crisis = True
        debt = rolls.d6(RollName.INJURY_DEBT) * 10_000
        for stat in zeroed_stats:
            injured[stat] = 1

    if entry.debt > 0:
        debt = entry.debt

    return Mishap(
        outcome=MishapOutcome(
            roll=mishap_roll,
            discharge_type=entry.discharge_type,
            imprisoned=entry.imprisoned,
            injury_reductions=injury_reductions,
            injury_crisis=injury_crisis,
        ),
        debt=debt,
        characteristics=injured,
    )
