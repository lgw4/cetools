from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from cetools.dice import Roller, parse_notation
from cetools.errors import RulesDataError, TaskError


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


def check(
    roller: Roller,
    *,
    difficulty: str | None = None,
    characteristic: int | None = None,
    skill: int | None = None,
    modifiers: Sequence[Modifier] = (),
    parameters: TaskParameters | None = None,
) -> CheckResult:
    """Resolve a 2D6 task check against `parameters` (the packaged rules by default).

    Modifiers are applied in fixed order: difficulty, characteristic (if
    given), skill, then the caller's `modifiers` in the order supplied.
    `difficulty=None` resolves through `parameters.default_difficulty()`;
    `skill=None` applies the unskilled penalty, while `skill=0` is trained
    at level 0.
    """
    if parameters is None:
        from cetools.rules import load_task_parameters

        parameters = load_task_parameters()

    count, sides, roll_modifier = parse_notation(parameters.roll)
    faces = roller.dice(count, sides)
    dice_total = sum(faces) + roll_modifier

    applied: list[Modifier] = []

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
    )
