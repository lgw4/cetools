from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol, TypeVar

T = TypeVar("T")


class RollName(StrEnum):
    """Every random decision the rules make.

    Read this enum and you know what the engine leaves to chance. Names exist so
    that a test can address a roll by intent ("survival fails in term 2") instead
    of by its position in a die sequence.
    """

    # Checks: 2D6 + DM >= target.
    QUALIFICATION = "qualification"
    SURVIVAL = "survival"
    COMMISSION = "commission"
    ADVANCEMENT = "advancement"
    PSI_GATE = "psi_gate"
    PSI_TALENT = "psi_talent"

    # Raw 2D6 values the rules do arithmetic on.
    CHARACTERISTIC = "characteristic"
    AGING = "aging"
    REENLISTMENT = "reenlistment"
    PSI_STRENGTH = "psi_strength"

    # 1D6 table indices and quantities.
    SKILL_TABLE = "skill_table"
    SKILL_ENTRY = "skill_entry"
    CASH_BENEFIT = "cash_benefit"
    MATERIAL_BENEFIT = "material_benefit"
    SHIP_SHARES = "ship_shares"
    DRAFT = "draft"
    MISHAP = "mishap"
    INJURY = "injury"
    INJURY_AMOUNT = "injury_amount"
    INJURY_DEBT = "injury_debt"

    # Uniform picks from a list.
    CAREER = "career"
    BACKGROUND_SKILL = "background_skill"
    INJURY_STAT = "injury_stat"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"


class Rolls(Protocol):
    """The engine's single seam for chance.

    Four verbs, because the rules only ever do four things. Callers compute their
    own DM: the seam knows about chance, not about characteristics.
    """

    def check(self, dm: int, target: int, name: RollName) -> bool:
        """Whether `2D6 + dm >= target` — the rule the whole engine runs on."""
        ...

    def two_d6(self, name: RollName) -> int:
        """A raw 2D6 value, for rules that do arithmetic on the total."""
        ...

    def d6(self, name: RollName) -> int:
        """A single die, 1-6: a table index or a quantity."""
        ...

    def choose(self, items: Sequence[T], name: RollName) -> T:
        """A uniform pick from `items`. Not a die roll: the list sets the range."""
        ...
