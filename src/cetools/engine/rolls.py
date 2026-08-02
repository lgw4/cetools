from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, TypeVar

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
    PLANETOID_BELT_PRESENCE = "planetoid_belt_presence"
    GAS_GIANT_PRESENCE = "gas_giant_presence"
    NAVAL_BASE = "naval_base"
    SCOUT_BASE = "scout_base"
    PIRATE_BASE = "pirate_base"

    # Raw 2D6 values the rules do arithmetic on.
    CHARACTERISTIC = "characteristic"
    AGING = "aging"
    REENLISTMENT = "reenlistment"
    PSI_STRENGTH = "psi_strength"
    WORLD_SIZE = "world_size"
    WORLD_ATMOSPHERE = "world_atmosphere"
    WORLD_HYDROGRAPHICS = "world_hydrographics"
    WORLD_POPULATION = "world_population"
    WORLD_GOVERNMENT = "world_government"
    WORLD_LAW_LEVEL = "world_law_level"
    WORLD_STARPORT = "world_starport"
    POPULATION_MODIFIER = "population_modifier"

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
    WORLD_TECH_LEVEL = "world_tech_level"
    PLANETOID_BELT_COUNT = "planetoid_belt_count"
    GAS_GIANT_COUNT = "gas_giant_count"
    WORLD_PRESENCE = "world_presence"

    # Uniform picks from a list.
    SKILL_TABLE = "skill_table"
    CAREER = "career"
    BACKGROUND_SKILL = "background_skill"
    INJURY_STAT = "injury_stat"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    WORLD_NAME_STEM = "world_name_stem"
    SHIP_HULL_SIZE = "ship_hull_size"
    SHIP_CONFIGURATION = "ship_configuration"
    SHIP_JUMP_CODE = "ship_jump_code"
    SHIP_MANEUVER_CODE = "ship_maneuver_code"
    SHIP_POWER_CODE = "ship_power_code"
    SHIP_ARMOR = "ship_armor"
    SHIP_COMPUTER = "ship_computer"
    SHIP_ELECTRONICS = "ship_electronics"
    SHIP_STATEROOMS = "ship_staterooms"
    SHIP_FITTING = "ship_fitting"
    SHIP_TURRET_COUNT = "ship_turret_count"
    SHIP_TURRET_MOUNT = "ship_turret_mount"
    SHIP_WEAPON = "ship_weapon"
    SHIP_COCKPIT = "ship_cockpit"
    SHIP_BAY = "ship_bay"
    SHIP_SCREEN = "ship_screen"
    SHIP_NAME = "ship_name"


class Rolls(Protocol):
    """The engine's single seam for chance.

    Four verbs, because the rules only ever do four things. Callers compute their
    own DM: the seam knows about chance, not about characteristics.
    """

    def check(self, dm: int, target: int, name: RollName) -> bool:
        """Whether `2D6 + dm >= target`—the rule the whole engine runs on."""
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

    @classmethod
    def seeded(cls, seed: int | None) -> RandomRolls:
        """Seeded for reproducibility, or unseeded (real entropy) when `seed` is None.

        The one place the optional-seed-to-adapter decision is made, so every entry
        point—each CLI command—gets reproducibility the same way.
        """
        return cls(random.Random(seed) if seed is not None else None)

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


@dataclass(frozen=True)
class Draw:
    """One question the engine put to the dice, and the answer it got back.

    `dm` and `target` are set for a check and nothing else; `offered` is set for a
    choose and nothing else. They are the arguments the *caller* supplied, which
    is the whole point: what the seam does with them is its own business and is
    tested against `RandomRolls`, but whether a caller handed over the right ones
    was not observable at all before this record existed.
    """

    verb: str
    name: RollName
    result: Any
    dm: int | None = None
    target: int | None = None
    offered: tuple[Any, ...] | None = None


class RecordingRolls:
    """A seam adapter that writes down every draw and delegates the answer.

    Wraps another adapter rather than replacing one, so a test records over real
    dice or scripted ones without changing what either would have returned::

        rolls = RecordingRolls(ScriptedRolls(checks={RollName.SURVIVAL: False}))
        generate(career, rolls)
        assert rolls.named(RollName.SURVIVAL)[0].target == career.survival_target

    Lives here rather than beside a test because three of these had already been
    written independently—one subclassing `ScriptedRolls` to count `choose` calls,
    one wrapping any adapter to log roll names, one spying a single `dm`—which is
    the seam reporting that observing a draw is a capability it owes its callers
    rather than a trick each test invents. `ScriptedRolls` answers *what the dice
    said*; this answers *what the engine asked*, and no other adapter can.
    """

    def __init__(self, inner: Rolls) -> None:
        self._inner = inner
        self._draws: list[Draw] = []

    @property
    def draws(self) -> tuple[Draw, ...]:
        """Every draw, in the order the engine made it."""
        return tuple(self._draws)

    def named(self, name: RollName) -> tuple[Draw, ...]:
        """Just the draws made under `name`, in order."""
        return tuple(draw for draw in self._draws if draw.name == name)

    def check(self, dm: int, target: int, name: RollName) -> bool:
        result = self._inner.check(dm, target, name)
        self._draws.append(Draw("check", name, result, dm=dm, target=target))
        return result

    def two_d6(self, name: RollName) -> int:
        result = self._inner.two_d6(name)
        self._draws.append(Draw("two_d6", name, result))
        return result

    def d6(self, name: RollName) -> int:
        result = self._inner.d6(name)
        self._draws.append(Draw("d6", name, result))
        return result

    def choose(self, items: Sequence[T], name: RollName) -> T:
        result = self._inner.choose(items, name)
        self._draws.append(Draw("choose", name, result, offered=tuple(items)))
        return result


MAX_ROLL_ATTEMPTS = 100
"""How many times a filtered draw retries before giving up.

Enough that real dice will never exhaust it; small enough that a degenerate rolls
source fails fast instead of hanging. See `bounded_retry`.
"""


def bounded_retry(
    produce: Callable[[], T],
    accept: Callable[[T], bool],
    *,
    attempts: int = MAX_ROLL_ATTEMPTS,
) -> T | None:
    """The first `produce()` an `accept` predicate likes, or `None` if none within budget.

    The guard for draws that filter their result. Real dice always land an
    acceptable value quickly, but a `ScriptedRolls` pinned to a rejected value
    (below a career's target, an already-used name, an exhausted once-only benefit)
    would otherwise spin for ever. Bounding the retries turns that into a loud,
    fast `None` the caller can fail on, rather than a hang. Callers decide what
    exhaustion means: `None` is safe here because every `produce` returns a real
    value, never `None`.
    """
    for _ in range(attempts):
        candidate = produce()
        if accept(candidate):
            return candidate
    return None
