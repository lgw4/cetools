from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cetools.dice import Roller, parse_notation
from cetools.errors import DiceError, RulesDataError, TaskError

if TYPE_CHECKING:
    from cetools.provenance import Provenance
    from cetools.rules import RulesData


def _check_dice(roll: str) -> tuple[int, int, int]:
    """Parse a `task.roll` value into `(count, sides, modifier)`.

    The single place a check's dice are read, so the loader and `check`
    itself cannot disagree about what `task.roll` may hold. Package-internal
    despite being imported by `rules.py`: the leading underscore is the
    convention `001-dice-task-engine/contracts/library-api.md` states for a
    seam callers outside the package must not use, and it is named there
    rather than in this feature's contract, so the reference has to say
    which. Raises
    `RulesDataError` for notation the grammar rejects and for the `d66`
    literal, which composes two faces into a two-digit table value rather
    than describing a count and a side count: a check needs the latter, and
    accepting it would surface as a `TypeError` that no `CetoolsError`
    handler catches (001-dice-task-engine FR-029).
    """
    try:
        parsed = parse_notation(roll)
    except DiceError as exc:
        raise RulesDataError(f"task.roll is not valid dice notation: {roll!r}") from exc
    if parsed is None:
        raise RulesDataError(
            f"task.roll must describe a count and a side count: {roll!r} is a "
            "two-digit table die and cannot describe a check's dice"
        )
    return parsed


@dataclass(frozen=True, slots=True)
class Band:
    """One row of the characteristic table.

    `maximum` is `None` for the sole unbounded top band, which sorts last.
    """

    minimum: int
    maximum: int | None
    dm: int


@dataclass(frozen=True, slots=True)
class TaskParameters:
    """The parsed contents of `tasks.toml`. Loaded once and cached."""

    roll: str
    target: int
    unskilled_dm: int
    difficulty_dms: Mapping[str, int]
    characteristic_bands: tuple[Band, ...]

    def difficulty_dm(self, name: str) -> int:
        try:
            return self.difficulty_dms[name]
        except KeyError:
            valid = ", ".join(self.difficulty_dms)
            raise TaskError(f"unknown difficulty {name!r}; valid names: {valid}") from None

    def default_difficulty(self) -> str:
        for name, value in self.difficulty_dms.items():
            if value == 0:
                return name
        raise RulesDataError("no difficulty rung has a modifier of 0")

    def characteristic_dm(self, score: int) -> int:
        if score < 0:
            raise TaskError(f"characteristic must be non-negative, got {score}")
        for band in self.characteristic_bands:
            if band.minimum <= score and (band.maximum is None or score <= band.maximum):
                return band.dm
        raise RulesDataError(f"no characteristic band covers score {score}")


@dataclass(frozen=True, slots=True)
class Modifier:
    """A single labeled adjustment to a check."""

    label: str
    value: int


@dataclass(frozen=True, slots=True)
class CheckResult:
    """The result of resolving a task check."""

    faces: tuple[int, ...]
    dice_total: int
    modifiers: tuple[Modifier, ...]
    total: int
    target: int
    success: bool
    seed: int
    provenance: Provenance


def check(
    roller: Roller,
    *,
    difficulty: str | None = None,
    characteristic: int | None = None,
    skill: int | None = None,
    modifiers: Sequence[Modifier] = (),
    rules: RulesData | None = None,
) -> CheckResult:
    """Resolve a 2D6 task check against `rules` (the packaged rules by default).

    Modifiers are applied in fixed order: difficulty, characteristic (if
    given), skill, then the caller's `modifiers` in the order supplied.
    `difficulty=None` resolves through `rules.task_parameters.default_difficulty()`;
    `skill=None` applies the unskilled penalty, while `skill=0` is trained
    at level 0. The returned `CheckResult` carries `rules.provenance`
    (002-rules-data-loading FR-037).

    A `task.roll` carrying a flat modifier (a house rule under
    001-dice-task-engine FR-022, since the shipped `2d6` has none) is itemized
    like every other modifier rather than folded into `dice_total`, which stays
    `sum(faces)` as data-model.md and contracts/json-output.md define it.
    001-dice-task-engine FR-018 requires every applied modifier to be itemized,
    and a `dice_total` that silently included one would make the rendered
    `(sum N)` false.
    """
    if rules is None:
        from cetools.rules import load_rules

        rules = load_rules()
    parameters = rules.task_parameters

    count, sides, roll_modifier = _check_dice(parameters.roll)
    faces = roller.dice(count, sides)
    dice_total = sum(faces)

    applied: list[Modifier] = []

    if roll_modifier:
        applied.append(Modifier(f"Roll ({parameters.roll})", roll_modifier))

    if difficulty is None:
        difficulty = parameters.default_difficulty()
    applied.append(Modifier(f"Difficulty ({difficulty})", parameters.difficulty_dm(difficulty)))

    if characteristic is not None:
        applied.append(
            Modifier(
                f"Characteristic {characteristic}", parameters.characteristic_dm(characteristic)
            )
        )

    if skill is None:
        applied.append(Modifier("Unskilled", parameters.unskilled_dm))
    else:
        if skill < 0:
            raise TaskError(f"skill must be non-negative, got {skill}")
        applied.append(Modifier(f"Skill {skill}", skill))

    applied.extend(modifiers)

    total = dice_total + sum(m.value for m in applied)
    return CheckResult(
        faces=faces,
        dice_total=dice_total,
        modifiers=tuple(applied),
        total=total,
        target=parameters.target,
        success=total >= parameters.target,
        seed=roller.seed,
        provenance=rules.provenance,
    )
