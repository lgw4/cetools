from __future__ import annotations

import random
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
    SKILL_TABLE = "skill_table"
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


class RandomRolls:
    """The production adapter: real dice, uniform picks."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random

    def _two_dice(self) -> int:
        return self._rng.randint(1, 6) + self._rng.randint(1, 6)

    def check(self, dm: int, target: int, name: RollName) -> bool:
        return self._two_dice() + dm >= target

    def two_d6(self, name: RollName) -> int:
        return self._two_dice()

    def d6(self, name: RollName) -> int:
        return self._rng.randint(1, 6)

    def choose(self, items: Sequence[T], name: RollName) -> T:
        if not items:
            raise ValueError(f"cannot choose from an empty sequence (roll '{name}')")
        return items[self._rng.randrange(len(items))]


class ScriptedRolls:
    """The test adapter: rolls addressed by name, not by position.

    Script only the rolls a test is actually about; everything else takes the
    per-verb default. A scalar means *always*; a list is consumed in order and
    then falls back to the default::

        ScriptedRolls(
            checks={RollName.SURVIVAL: [True, False]},  # survive term 1, fail term 2
            d6={RollName.MISHAP: 4},                    # always a dishonorable discharge
        )

    A scripted `check` supplies the *outcome*, not the dice: the `2D6 + DM >=
    target` arithmetic is the seam's job and is tested there once.

    `choices` are 0-based indices into whatever list the engine offers, so a
    negative index picks from the end. `two_d6[CHARACTERISTIC]` takes a list in
    ``STAT_NAMES`` order.
    """

    def __init__(
        self,
        *,
        checks: dict[RollName, bool | list[bool]] | None = None,
        two_d6: dict[RollName, int | list[int]] | None = None,
        d6: dict[RollName, int | list[int]] | None = None,
        choices: dict[RollName, int | list[int]] | None = None,
        default_check: bool = True,
        default_two_d6: int = 7,
        default_d6: int = 1,
        default_choice: int = 0,
    ) -> None:
        self._checks = self._script(checks)
        self._two_d6 = self._script(two_d6)
        self._d6 = self._script(d6)
        self._choices = self._script(choices)
        self._default_check = default_check
        self._default_two_d6 = default_two_d6
        self._default_d6 = default_d6
        self._default_choice = default_choice

    @staticmethod
    def _script(spec: dict | None) -> dict:
        scripted = {}
        for name, value in (spec or {}).items():
            if not isinstance(name, RollName):
                raise TypeError(f"scripted roll keys must be RollName members, got {name!r}")
            scripted[name] = list(value) if isinstance(value, list) else value
        return scripted

    @staticmethod
    def _next(scripted: dict, name: RollName, default):
        if name not in scripted:
            return default
        value = scripted[name]
        if not isinstance(value, list):
            return value  # a scalar means always
        return value.pop(0) if value else default

    def check(self, dm: int, target: int, name: RollName) -> bool:
        return bool(self._next(self._checks, name, self._default_check))

    def two_d6(self, name: RollName) -> int:
        return self._next(self._two_d6, name, self._default_two_d6)

    def d6(self, name: RollName) -> int:
        return self._next(self._d6, name, self._default_d6)

    def choose(self, items: Sequence[T], name: RollName) -> T:
        if not items:
            raise ValueError(f"cannot choose from an empty sequence (roll '{name}')")
        return items[self._next(self._choices, name, self._default_choice) % len(items)]
