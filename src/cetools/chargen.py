"""The universal chargen tables: draft, aging, mishaps, background skills,
medical tiers, and the parameters the walk reads everything else from
(contracts/data-files.md, data-model.md).

Each `parse_*` function turns one file's already-parsed TOML dict into a
table, collecting every problem rather than raising on the first, following
the convention `registries.py` and `careers.py` established.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cetools.errors import RulesDataError, ValidationProblem, type_name
from cetools.notation import EntryContext, NotationProblem, SkillGrant, parse_entry
from cetools.registries import SkillRegistry, SkillResolution
from cetools.tasks import _check_dice

_HEADER_KEYS = frozenset({"schema", "schema-version"})

_RANGE_SINGLE = re.compile(r"^(-?\d+)$")
_RANGE_BOUNDED = re.compile(r"^(-?\d+)-(-?\d+)$")
_RANGE_UNBOUNDED = re.compile(r"^(-?\d+)\+$")

_AMOUNT_INTEGER = re.compile(r"^[+-]?\d+$")
_AMOUNT_DICE = re.compile(r"^[+-]?\d*[dD]\d+(?:[+-]\d+)?$")


def _unrecognized_key_problems(
    data: Mapping[str, object], allowed: frozenset[str], file: str, prefix: str = ""
) -> list[ValidationProblem]:
    extra = sorted(set(data) - allowed)
    return [
        ValidationProblem(
            file=file,
            location=f"{prefix}{key}",
            found=f"unrecognized key {key!r}",
            expected=f"one of: {', '.join(sorted(allowed))}",
        )
        for key in extra
    ]


def _require_roll(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None:
    """A dice-notation field, rejecting `d66` for the same reason
    `task.roll` does: the row a chargen table reads is the throw's total, and
    `d66` composes two faces into a two-digit table value rather than
    describing a count and a side count (001-dice-task-engine FR-029).
    """
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="a string")
        )
        return None
    value = container[key]
    if not isinstance(value, str):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a string"
            )
        )
        return None
    try:
        _check_dice(value)
    except RulesDataError as exc:
        problems.append(
            ValidationProblem(file=file, location=location, found=repr(value), expected=str(exc))
        )
        return None
    return value


def _require_int(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
    *,
    minimum: int | None = None,
) -> int | None:
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="an integer")
        )
        return None
    value = container[key]
    if not isinstance(value, int) or isinstance(value, bool):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="an integer"
            )
        )
        return None
    if minimum is not None and value < minimum:
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found=str(value),
                expected=f"an integer >= {minimum}",
            )
        )
        return None
    return value


def _require_string(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None:
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="a string")
        )
        return None
    value = container[key]
    if not isinstance(value, str) or not value:
        found = type_name(value) if not isinstance(value, str) else "an empty string"
        problems.append(
            ValidationProblem(
                file=file, location=location, found=found, expected="a non-empty string"
            )
        )
        return None
    return value


def _require_bool(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> bool | None:
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="a boolean")
        )
        return None
    value = container[key]
    if not isinstance(value, bool):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a boolean"
            )
        )
        return None
    return value


# --- draft-table (contracts/data-files.md) ----------------------------------


@dataclass(frozen=True, slots=True)
class DraftTable:
    """`roll` reads a row of `careers` positionally; row order is
    significant because the die is positional (FR-005).
    """

    roll: str
    careers: tuple[str, ...]


def parse_draft_table(
    data: Mapping[str, object], file: str
) -> tuple[DraftTable | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(_unrecognized_key_problems(data, _HEADER_KEYS | {"roll", "careers"}, file))

    roll = _require_roll(data, "roll", file, "roll", problems)

    careers: tuple[str, ...] | None = None
    if "careers" not in data:
        problems.append(
            ValidationProblem(
                file=file, location="careers", found="missing", expected="a non-empty array"
            )
        )
    else:
        raw = data["careers"]
        if not isinstance(raw, list) or not raw:
            found = type_name(raw) if not isinstance(raw, list) else "an empty array"
            problems.append(
                ValidationProblem(
                    file=file, location="careers", found=found, expected="at least one entry"
                )
            )
        else:
            parsed: list[str] = []
            ok = True
            for index, item in enumerate(raw):
                if not isinstance(item, str) or not item:
                    found = type_name(item) if not isinstance(item, str) else "an empty string"
                    problems.append(
                        ValidationProblem(
                            file=file,
                            location=f"careers[{index}]",
                            found=found,
                            expected="a non-empty string",
                        )
                    )
                    ok = False
                    continue
                parsed.append(item)
            if ok:
                careers = tuple(parsed)

    if problems or roll is None or careers is None:
        return None, tuple(problems)
    return DraftTable(roll=roll, careers=careers), ()


# --- aging-table (contracts/data-files.md) -----------------------------------


@dataclass(frozen=True, slots=True)
class ClassEffect:
    """Reduce `count` distinct characteristics of `characteristic_class` by
    `amount`. Which characteristics are chosen is the generator's decision,
    made at random and recorded in the history.
    """

    characteristic_class: str
    count: int
    amount: int


@dataclass(frozen=True, slots=True)
class AgingRow:
    """`maximum` is `None` for the sole unbounded top row. The lowest row is
    a floor: a modified result below it reads that row.
    """

    minimum: int
    maximum: int | None
    effects: tuple[ClassEffect, ...]


@dataclass(frozen=True, slots=True)
class AgingTable:
    """`rows` sorted by `minimum`, exactly one unbounded above."""

    roll: str
    rows: tuple[AgingRow, ...]


def _parse_range(text: str) -> tuple[int, int | None] | None:
    """`N`, `N-M`, or `N+`, any of which may be negative."""
    if (match := _RANGE_UNBOUNDED.match(text)) is not None:
        return int(match.group(1)), None
    if (match := _RANGE_BOUNDED.match(text)) is not None:
        return int(match.group(1)), int(match.group(2))
    if (match := _RANGE_SINGLE.match(text)) is not None:
        value = int(match.group(1))
        return value, value
    return None


def _parse_class_effect(
    value: object, file: str, location: str
) -> tuple[ClassEffect | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(
        _unrecognized_key_problems(value, {"class", "count", "amount"}, file, f"{location}.")
    )

    characteristic_class = _require_string(value, "class", file, f"{location}.class", problems)
    count = _require_int(value, "count", file, f"{location}.count", problems, minimum=1)

    amount = None
    if "amount" not in value:
        problems.append(
            ValidationProblem(
                file=file, location=f"{location}.amount", found="missing", expected="an integer"
            )
        )
    else:
        raw_amount = value["amount"]
        if not isinstance(raw_amount, int) or isinstance(raw_amount, bool):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.amount",
                    found=type_name(raw_amount),
                    expected="an integer",
                )
            )
        elif raw_amount == 0:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.amount",
                    found="0",
                    expected="a signed, non-zero integer",
                )
            )
        else:
            amount = raw_amount

    if characteristic_class is None or count is None or amount is None:
        return None, problems
    return (
        ClassEffect(characteristic_class=characteristic_class, count=count, amount=amount),
        problems,
    )


def _parse_effects(
    raw: object, file: str, location: str
) -> tuple[tuple[ClassEffect, ...] | None, list[ValidationProblem]]:
    if not isinstance(raw, list):
        return None, [
            ValidationProblem(
                file=file, location=location, found=type_name(raw), expected="an array"
            )
        ]
    problems: list[ValidationProblem] = []
    effects: list[ClassEffect] = []
    ok = True
    for index, item in enumerate(raw):
        effect, sub_problems = _parse_class_effect(item, file, f"{location}[{index}]")
        problems.extend(sub_problems)
        if effect is None:
            ok = False
        else:
            effects.append(effect)
    if not ok:
        return None, problems
    return tuple(effects), problems


def _parse_aging_row(
    value: object, file: str, location: str
) -> tuple[AgingRow | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(_unrecognized_key_problems(value, {"range", "effects"}, file, f"{location}."))

    bounds: tuple[int, int | None] | None = None
    range_text = _require_string(value, "range", file, f"{location}.range", problems)
    if range_text is not None:
        bounds = _parse_range(range_text)
        if bounds is None:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.range",
                    found=repr(range_text),
                    expected="N, N-M, or N+",
                )
            )

    effects: tuple[ClassEffect, ...] | None = None
    if "effects" not in value:
        problems.append(
            ValidationProblem(
                file=file, location=f"{location}.effects", found="missing", expected="an array"
            )
        )
    else:
        effects, sub_problems = _parse_effects(value["effects"], file, f"{location}.effects")
        problems.extend(sub_problems)

    if bounds is None or effects is None:
        return None, problems
    minimum, maximum = bounds
    return AgingRow(minimum=minimum, maximum=maximum, effects=effects), problems


def parse_aging_table(
    data: Mapping[str, object], file: str
) -> tuple[AgingTable | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(
        _unrecognized_key_problems(data, _HEADER_KEYS | {"roll", "modifier", "rows"}, file)
    )

    roll = _require_roll(data, "roll", file, "roll", problems)

    modifier = data.get("modifier")
    if modifier != "terms-served":
        problems.append(
            ValidationProblem(
                file=file,
                location="modifier",
                found="missing" if "modifier" not in data else repr(modifier),
                expected="'terms-served'",
            )
        )

    rows: list[AgingRow] | None = None
    if "rows" not in data:
        problems.append(
            ValidationProblem(file=file, location="rows", found="missing", expected="an array")
        )
    else:
        raw_rows = data["rows"]
        if not isinstance(raw_rows, list) or not raw_rows:
            found = type_name(raw_rows) if not isinstance(raw_rows, list) else "an empty array"
            problems.append(
                ValidationProblem(
                    file=file, location="rows", found=found, expected="at least one row"
                )
            )
        else:
            parsed_rows: list[AgingRow] = []
            ok = True
            for index, item in enumerate(raw_rows):
                row, sub_problems = _parse_aging_row(item, file, f"rows[{index}]")
                problems.extend(sub_problems)
                if row is None:
                    ok = False
                else:
                    parsed_rows.append(row)
            if ok:
                rows = parsed_rows

    if rows is not None:
        unbounded_count = sum(1 for row in rows if row.maximum is None)
        if unbounded_count != 1:
            problems.append(
                ValidationProblem(
                    file=file,
                    location="rows",
                    found=f"{unbounded_count} unbounded rows",
                    expected="exactly one row unbounded above",
                )
            )
            rows = None

    if problems or roll is None or rows is None:
        return None, tuple(problems)
    rows.sort(key=lambda row: row.minimum)
    return AgingTable(roll=roll, rows=tuple(rows)), ()


# --- mishap-table (contracts/data-files.md) ----------------------------------

_MISHAP_EFFECT_KINDS = frozenset(
    {
        "characteristic-class",
        "debt",
        "years",
        "forfeit-term-benefit",
        "forfeit-career-benefits",
        "roll-injury",
    }
)
_MISHAP_EFFECT_AMOUNT_KINDS = frozenset({"characteristic-class", "debt", "years"})


@dataclass(frozen=True, slots=True)
class MishapEffect:
    """One consequence of a mishap or an injury row.

    `characteristic_class` and `count` are only meaningful for
    `"characteristic-class"`, `""` and `0` otherwise; `amount` is only
    meaningful for `"characteristic-class"`, `"debt"`, and `"years"`, `""`
    otherwise.
    """

    kind: str
    characteristic_class: str
    count: int
    amount: str


@dataclass(frozen=True, slots=True)
class MishapRow:
    """One row of the mishap table, indexed by the throw's total, like the
    draft table.
    """

    description: str
    effects: tuple[MishapEffect, ...]


@dataclass(frozen=True, slots=True)
class InjuryRow:
    """One row of the injury table, reached only from a `roll-injury`
    effect.
    """

    description: str
    effects: tuple[MishapEffect, ...]


@dataclass(frozen=True, slots=True)
class MishapTable:
    """`rows` from `mishaps`, indexed positionally by `roll`'s total.
    `injuries` lives here because nothing but a `roll-injury` effect reaches
    it, and splitting the two files would let a referee replace one and
    leave a dangling reference in the other.
    """

    roll: str
    rows: tuple[MishapRow, ...]
    injury_roll: str
    injuries: tuple[InjuryRow, ...]


def _valid_amount_text(text: str) -> bool:
    return bool(_AMOUNT_INTEGER.match(text) or _AMOUNT_DICE.match(text))


def _parse_mishap_effect(
    value: object, file: str, location: str
) -> tuple[MishapEffect | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    kind = value.get("kind")
    if kind not in _MISHAP_EFFECT_KINDS:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.kind",
                found="missing" if "kind" not in value else repr(kind),
                expected=f"one of: {', '.join(sorted(_MISHAP_EFFECT_KINDS))}",
            )
        )
        problems.extend(
            _unrecognized_key_problems(
                value, {"kind", "class", "count", "amount"}, file, f"{location}."
            )
        )
        return None, problems

    allowed = {"kind"}
    if kind == "characteristic-class":
        allowed |= {"class", "count", "amount"}
    elif kind in ("debt", "years"):
        allowed |= {"amount"}
    problems.extend(_unrecognized_key_problems(value, allowed, file, f"{location}."))

    characteristic_class = ""
    count = 0
    if kind == "characteristic-class":
        parsed_class = _require_string(value, "class", file, f"{location}.class", problems)
        parsed_count = _require_int(value, "count", file, f"{location}.count", problems, minimum=1)
        characteristic_class = parsed_class or ""
        count = parsed_count if parsed_count is not None else 0

    amount = ""
    if kind in _MISHAP_EFFECT_AMOUNT_KINDS:
        raw_amount = value.get("amount")
        if not isinstance(raw_amount, str) or not raw_amount:
            found = "missing" if "amount" not in value else type_name(raw_amount)
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.amount",
                    found=found,
                    expected="dice notation or a signed integer, as text",
                )
            )
        elif not _valid_amount_text(raw_amount):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.amount",
                    found=repr(raw_amount),
                    expected="dice notation or a signed integer, as text",
                )
            )
        else:
            amount = raw_amount

    if problems:
        return None, problems
    return (
        MishapEffect(
            kind=kind, characteristic_class=characteristic_class, count=count, amount=amount
        ),
        problems,
    )


def _parse_mishap_effects(
    raw: object, file: str, location: str
) -> tuple[tuple[MishapEffect, ...] | None, list[ValidationProblem]]:
    if not isinstance(raw, list):
        return None, [
            ValidationProblem(
                file=file, location=location, found=type_name(raw), expected="an array"
            )
        ]
    problems: list[ValidationProblem] = []
    effects: list[MishapEffect] = []
    ok = True
    for index, item in enumerate(raw):
        effect, sub_problems = _parse_mishap_effect(item, file, f"{location}[{index}]")
        problems.extend(sub_problems)
        if effect is None:
            ok = False
        else:
            effects.append(effect)
    if not ok:
        return None, problems
    return tuple(effects), problems


def _parse_mishap_row(
    value: object, file: str, location: str
) -> tuple[tuple[str, tuple[MishapEffect, ...]] | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(
        _unrecognized_key_problems(value, {"description", "effects"}, file, f"{location}.")
    )

    description = _require_string(value, "description", file, f"{location}.description", problems)

    effects: tuple[MishapEffect, ...] | None = None
    if "effects" not in value:
        problems.append(
            ValidationProblem(
                file=file, location=f"{location}.effects", found="missing", expected="an array"
            )
        )
    else:
        effects, sub_problems = _parse_mishap_effects(
            value["effects"], file, f"{location}.effects"
        )
        problems.extend(sub_problems)

    if description is None or effects is None:
        return None, problems
    return (description, effects), problems


def _parse_row_array(
    raw: object, file: str, location: str
) -> tuple[list[tuple[str, tuple[MishapEffect, ...]]] | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(raw, list) or not raw:
        found = type_name(raw) if not isinstance(raw, list) else "an empty array"
        problems.append(
            ValidationProblem(
                file=file, location=location, found=found, expected="at least one row"
            )
        )
        return None, problems

    rows: list[tuple[str, tuple[MishapEffect, ...]]] = []
    ok = True
    for index, item in enumerate(raw):
        row, sub_problems = _parse_mishap_row(item, file, f"{location}[{index}]")
        problems.extend(sub_problems)
        if row is None:
            ok = False
        else:
            rows.append(row)
    if not ok:
        return None, problems
    return rows, problems


def parse_mishap_table(
    data: Mapping[str, object], file: str
) -> tuple[MishapTable | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(
        _unrecognized_key_problems(
            data, _HEADER_KEYS | {"roll", "injury-roll", "mishaps", "injuries"}, file
        )
    )

    roll = _require_roll(data, "roll", file, "roll", problems)
    injury_roll = _require_roll(data, "injury-roll", file, "injury-roll", problems)

    mishaps: list[tuple[str, tuple[MishapEffect, ...]]] | None = None
    if "mishaps" not in data:
        problems.append(
            ValidationProblem(file=file, location="mishaps", found="missing", expected="an array")
        )
    else:
        mishaps, sub_problems = _parse_row_array(data["mishaps"], file, "mishaps")
        problems.extend(sub_problems)

    injuries: list[tuple[str, tuple[MishapEffect, ...]]] | None = None
    if "injuries" not in data:
        problems.append(
            ValidationProblem(file=file, location="injuries", found="missing", expected="an array")
        )
    else:
        injuries, sub_problems = _parse_row_array(data["injuries"], file, "injuries")
        problems.extend(sub_problems)

    if problems or roll is None or injury_roll is None or mishaps is None or injuries is None:
        return None, tuple(problems)
    return (
        MishapTable(
            roll=roll,
            rows=tuple(MishapRow(description=d, effects=e) for d, e in mishaps),
            injury_roll=injury_roll,
            injuries=tuple(InjuryRow(description=d, effects=e) for d, e in injuries),
        ),
        (),
    )


# --- background-skills (contracts/data-files.md) -----------------------------


@dataclass(frozen=True, slots=True)
class BackgroundSkills:
    """The homeworld draw is uniform over the concatenation of `law_level`
    and `trade_code`; duplicates within and across those two lists are
    preserved and meaningful (research R5): a skill named by three trade
    codes is three times as likely as one named by a single code.
    """

    law_level: tuple[SkillGrant, ...]
    trade_code: tuple[SkillGrant, ...]
    education: tuple[SkillGrant, ...]


def _parse_skill_grant(
    text: object, file: str, location: str, skills: SkillRegistry
) -> tuple[SkillGrant | None, ValidationProblem | None]:
    if not isinstance(text, str):
        return None, ValidationProblem(
            file=file, location=location, found=type_name(text), expected="a notation string"
        )

    parsed = parse_entry(text, EntryContext.SKILL_TABLE)
    if isinstance(parsed, NotationProblem):
        return None, ValidationProblem(
            file=file, location=location, found=parsed.found, expected=parsed.expected
        )
    if not isinstance(parsed, SkillGrant):
        return None, ValidationProblem(
            file=file,
            location=location,
            found=text,
            expected="a skill granted at an explicit level, e.g. 'Gun Combat 0'",
        )

    resolution = skills.resolve(parsed.skill)
    if resolution is SkillResolution.VALID:
        return parsed, None
    reference = parsed.skill
    if resolution is SkillResolution.UNRECOGNIZED_SKILL:
        found = (
            f"{reference.name} ({reference.specialty})"
            if reference.specialty is not None
            else reference.name
        )
        expected = "a name in the skills registry"
    elif resolution is SkillResolution.SPECIALTY_NOT_ALLOWED:
        found = f"{reference.name} ({reference.specialty})"
        expected = f"a bare {reference.name}: the skills registry gives it no specialties"
    else:
        found = f"{reference.name} ({reference.specialty})"
        expected = f"a specialty the skills registry gives {reference.name}"
    return None, ValidationProblem(file=file, location=location, found=found, expected=expected)


def _parse_skill_grant_list(
    raw: object, file: str, location: str, skills: SkillRegistry
) -> tuple[tuple[SkillGrant, ...] | None, list[ValidationProblem]]:
    if not isinstance(raw, list) or not raw:
        found = type_name(raw) if not isinstance(raw, list) else "an empty array"
        return None, [
            ValidationProblem(
                file=file, location=location, found=found, expected="at least one entry"
            )
        ]

    problems: list[ValidationProblem] = []
    grants: list[SkillGrant] = []
    ok = True
    for index, item in enumerate(raw):
        grant, problem = _parse_skill_grant(item, file, f"{location}[{index}]", skills)
        if problem is not None:
            problems.append(problem)
            ok = False
        else:
            grants.append(grant)
    if not ok:
        return None, problems
    return tuple(grants), problems


def parse_background_skills(
    data: Mapping[str, object], file: str, skills: SkillRegistry
) -> tuple[BackgroundSkills | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(
        _unrecognized_key_problems(
            data, _HEADER_KEYS | {"law-level", "trade-code", "education"}, file
        )
    )

    lists: dict[str, tuple[SkillGrant, ...] | None] = {}
    for key in ("law-level", "trade-code", "education"):
        if key not in data:
            problems.append(
                ValidationProblem(file=file, location=key, found="missing", expected="an array")
            )
            lists[key] = None
            continue
        parsed, sub_problems = _parse_skill_grant_list(data[key], file, key, skills)
        problems.extend(sub_problems)
        lists[key] = parsed

    if problems or any(value is None for value in lists.values()):
        return None, tuple(problems)
    return (
        BackgroundSkills(
            law_level=lists["law-level"],
            trade_code=lists["trade-code"],
            education=lists["education"],
        ),
        (),
    )


# --- medical-tiers (contracts/data-files.md) ---------------------------------


@dataclass(frozen=True, slots=True)
class MedicalThreshold:
    """The modified total must equal or exceed `target` for `paid_percent`
    to apply. A total below every threshold in a tier pays nothing.
    """

    target: int
    paid_percent: int


@dataclass(frozen=True, slots=True)
class MedicalTiers:
    """`rank_dm` is declared rather than assumed: whether the character's
    rank is added to the total. `tiers` is keyed by name, each tier's
    thresholds sorted highest-target-first so the first match wins.
    """

    roll: str
    rank_dm: bool
    tiers: Mapping[str, tuple[MedicalThreshold, ...]]


def _parse_medical_threshold(
    value: object, file: str, location: str
) -> tuple[MedicalThreshold | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(
        _unrecognized_key_problems(value, {"target", "paid-percent"}, file, f"{location}.")
    )

    target = _require_int(value, "target", file, f"{location}.target", problems, minimum=0)
    paid_percent = _require_int(
        value, "paid-percent", file, f"{location}.paid-percent", problems, minimum=0
    )
    if paid_percent is not None and paid_percent > 100:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.paid-percent",
                found=str(paid_percent),
                expected="an integer between 0 and 100",
            )
        )
        paid_percent = None

    if target is None or paid_percent is None:
        return None, problems
    return MedicalThreshold(target=target, paid_percent=paid_percent), problems


def _parse_tier(
    value: object, file: str, location: str
) -> tuple[tuple[str, tuple[MedicalThreshold, ...]] | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(
        _unrecognized_key_problems(value, {"name", "thresholds"}, file, f"{location}.")
    )

    name = _require_string(value, "name", file, f"{location}.name", problems)

    thresholds: list[MedicalThreshold] | None = None
    if "thresholds" not in value:
        problems.append(
            ValidationProblem(
                file=file, location=f"{location}.thresholds", found="missing", expected="an array"
            )
        )
    else:
        raw = value["thresholds"]
        if not isinstance(raw, list) or not raw:
            found = type_name(raw) if not isinstance(raw, list) else "an empty array"
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.thresholds",
                    found=found,
                    expected="at least one entry",
                )
            )
        else:
            parsed: list[MedicalThreshold] = []
            ok = True
            targets_seen: set[int] = set()
            for index, item in enumerate(raw):
                threshold, sub_problems = _parse_medical_threshold(
                    item, file, f"{location}.thresholds[{index}]"
                )
                problems.extend(sub_problems)
                if threshold is None:
                    ok = False
                    continue
                if threshold.target in targets_seen:
                    problems.append(
                        ValidationProblem(
                            file=file,
                            location=f"{location}.thresholds[{index}].target",
                            found=str(threshold.target),
                            expected="a target distinct within its tier",
                        )
                    )
                    ok = False
                    continue
                targets_seen.add(threshold.target)
                parsed.append(threshold)
            if ok:
                thresholds = parsed

    if name is None or thresholds is None:
        return None, problems
    thresholds.sort(key=lambda threshold: threshold.target, reverse=True)
    return (name, tuple(thresholds)), problems


def parse_medical_tiers(
    data: Mapping[str, object], file: str
) -> tuple[MedicalTiers | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(
        _unrecognized_key_problems(data, _HEADER_KEYS | {"roll", "rank-dm", "tiers"}, file)
    )

    roll = _require_roll(data, "roll", file, "roll", problems)
    rank_dm = _require_bool(data, "rank-dm", file, "rank-dm", problems)

    tiers: dict[str, tuple[MedicalThreshold, ...]] | None = None
    if "tiers" not in data:
        problems.append(
            ValidationProblem(file=file, location="tiers", found="missing", expected="an array")
        )
    else:
        raw = data["tiers"]
        if not isinstance(raw, list) or not raw:
            found = type_name(raw) if not isinstance(raw, list) else "an empty array"
            problems.append(
                ValidationProblem(
                    file=file, location="tiers", found=found, expected="at least one entry"
                )
            )
        else:
            parsed: dict[str, tuple[MedicalThreshold, ...]] = {}
            ok = True
            for index, item in enumerate(raw):
                result, sub_problems = _parse_tier(item, file, f"tiers[{index}]")
                problems.extend(sub_problems)
                if result is None:
                    ok = False
                    continue
                name, thresholds = result
                if name in parsed:
                    problems.append(
                        ValidationProblem(
                            file=file,
                            location=f"tiers[{index}].name",
                            found=f"both declare the name {name!r}",
                            expected="a name distinct across tiers",
                        )
                    )
                    ok = False
                    continue
                parsed[name] = thresholds
            if ok:
                tiers = parsed

    if problems or roll is None or rank_dm is None or tiers is None:
        return None, tuple(problems)
    return MedicalTiers(roll=roll, rank_dm=rank_dm, tiers=MappingProxyType(tiers)), ()


# --- chargen-parameters (contracts/data-files.md) ----------------------------

# Every scalar the walk depends on (FR-038), grouped exactly as the file
# groups them. `(kind, minimum)`: `kind` is "roll", "int", "bool", or
# "string"; `minimum` bounds an integer field, `None` where the field is a
# signed modifier with no natural floor. Declarative, so ChargenParameters
# exposes every one of these as a named attribute — a misspelling in this
# table is an `AttributeError` at import, not a `KeyError` mid-walk — without
# forty near-identical `_require_*` call sites to keep in sync with it.
_CHARGEN_GROUPS: dict[str, dict[str, tuple[str, int | None]]] = {
    "characteristics": {"roll": ("roll", None)},
    "background-skills": {
        "base": ("int", 0),
        "characteristic": ("string", None),
        "homeworld-first": ("int", 0),
    },
    "terms": {
        "starting-age": ("int", 0),
        "term-years": ("int", 1),
        "mishap-term-years": ("int", 1),
        "cap": ("int", 1),
        "aging-begins-at-age": ("int", 0),
    },
    "qualification": {
        "penalty-per-previous-career": ("int", None),
        "draft-entries-allowed": ("int", 0),
    },
    "basic-training": {
        "first-career-all": ("bool", None),
        "subsequent-career-count": ("int", 0),
    },
    "survival": {"natural-failure": ("int", 0)},
    "skill-rolls": {
        "per-term": ("int", 0),
        "per-term-without-throws": ("int", 0),
        "on-commission": ("int", 0),
        "on-advancement": ("int", 0),
    },
    "commission": {"drafted-first-term-barred": ("bool", None)},
    "continuation": {"roll": ("roll", None), "target": ("int", 0)},
    "mustering-out": {
        "roll": ("roll", None),
        "cash-choice-roll": ("roll", None),
        "cash-choice-target": ("int", 0),
        "maximum-cash-rolls": ("int", 0),
        "retired-cash-dm": ("int", None),
    },
    "pension": {
        "minimum-terms": ("int", 1),
        "base": ("int", 0),
        "per-additional-term": ("int", 0),
    },
    "medical": {
        "crisis-roll": ("roll", None),
        "crisis-multiplier": ("int", 0),
        "crisis-restores-to": ("int", 0),
        "restore-cost-per-point": ("int", 0),
    },
}

# The two mustering-out fields that are arrays of rank-scoped rows rather
# than scalars, keyed by the row's own value field name.
_RANK_BONUS_ARRAYS = {"rank-benefits": "extra", "material-rank-dm": "dm"}


def _chargen_attribute(group: str, key: str) -> str:
    return f"{group.replace('-', '_')}_{key.replace('-', '_')}"


@dataclass(frozen=True, slots=True)
class RankBonus:
    """One row of `mustering-out.rank-benefits` or `.material-rank-dm`: at
    `rank` or above, `amount` applies. The highest matching row wins;
    neither table is cumulative.
    """

    rank: int
    amount: int


@dataclass(frozen=True, slots=True)
class ChargenParameters:
    """Every rules constant the walk depends on, exposed as named
    attributes rather than as a nested mapping (FR-038).
    """

    characteristics_roll: str
    background_skills_base: int
    background_skills_characteristic: str
    background_skills_homeworld_first: int
    terms_starting_age: int
    terms_term_years: int
    terms_mishap_term_years: int
    terms_cap: int
    terms_aging_begins_at_age: int
    qualification_penalty_per_previous_career: int
    qualification_draft_entries_allowed: int
    basic_training_first_career_all: bool
    basic_training_subsequent_career_count: int
    survival_natural_failure: int
    skill_rolls_per_term: int
    skill_rolls_per_term_without_throws: int
    skill_rolls_on_commission: int
    skill_rolls_on_advancement: int
    commission_drafted_first_term_barred: bool
    continuation_roll: str
    continuation_target: int
    mustering_out_roll: str
    mustering_out_cash_choice_roll: str
    mustering_out_cash_choice_target: int
    mustering_out_maximum_cash_rolls: int
    mustering_out_retired_cash_dm: int
    mustering_out_rank_benefits: tuple[RankBonus, ...]
    mustering_out_material_rank_dm: tuple[RankBonus, ...]
    pension_minimum_terms: int
    pension_base: int
    pension_per_additional_term: int
    medical_crisis_roll: str
    medical_crisis_multiplier: int
    medical_crisis_restores_to: int
    medical_restore_cost_per_point: int


def _parse_rank_bonus(
    value: object, file: str, location: str, value_key: str
) -> tuple[RankBonus | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(_unrecognized_key_problems(value, {"rank", value_key}, file, f"{location}."))
    rank = _require_int(value, "rank", file, f"{location}.rank", problems, minimum=0)
    amount = _require_int(value, value_key, file, f"{location}.{value_key}", problems)

    if rank is None or amount is None:
        return None, problems
    return RankBonus(rank=rank, amount=amount), problems


def _parse_rank_bonus_list(
    raw: object, file: str, location: str, value_key: str
) -> tuple[tuple[RankBonus, ...] | None, list[ValidationProblem]]:
    if not isinstance(raw, list) or not raw:
        found = type_name(raw) if not isinstance(raw, list) else "an empty array"
        return None, [
            ValidationProblem(
                file=file, location=location, found=found, expected="at least one entry"
            )
        ]
    problems: list[ValidationProblem] = []
    bonuses: list[RankBonus] = []
    ok = True
    for index, item in enumerate(raw):
        bonus, sub_problems = _parse_rank_bonus(item, file, f"{location}[{index}]", value_key)
        problems.extend(sub_problems)
        if bonus is None:
            ok = False
        else:
            bonuses.append(bonus)
    if not ok:
        return None, problems
    return tuple(bonuses), problems


def _parse_chargen_group(
    data: Mapping[str, object], group: str, file: str, problems: list[ValidationProblem]
) -> dict[str, object]:
    location = group
    fields = _CHARGEN_GROUPS[group]
    allowed = set(fields)
    if group == "mustering-out":
        allowed |= set(_RANK_BONUS_ARRAYS)

    table = data.get(group)
    if not isinstance(table, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found="missing" if group not in data else type_name(table),
                expected="a table",
            )
        )
        return {}

    problems.extend(_unrecognized_key_problems(table, allowed, file, f"{location}."))

    values: dict[str, object] = {}
    for key, (kind, minimum) in fields.items():
        field_location = f"{location}.{key}"
        attribute = _chargen_attribute(group, key)
        if kind == "roll":
            values[attribute] = _require_roll(table, key, file, field_location, problems)
        elif kind == "bool":
            values[attribute] = _require_bool(table, key, file, field_location, problems)
        elif kind == "string":
            values[attribute] = _require_string(table, key, file, field_location, problems)
        else:
            values[attribute] = _require_int(
                table, key, file, field_location, problems, minimum=minimum
            )

    if group == "mustering-out":
        for array_key, value_key in _RANK_BONUS_ARRAYS.items():
            field_location = f"{location}.{array_key}"
            attribute = _chargen_attribute(group, array_key)
            if array_key not in table:
                problems.append(
                    ValidationProblem(
                        file=file, location=field_location, found="missing", expected="an array"
                    )
                )
                values[attribute] = None
                continue
            parsed, sub_problems = _parse_rank_bonus_list(
                table[array_key], file, field_location, value_key
            )
            problems.extend(sub_problems)
            values[attribute] = parsed

    return values


def parse_chargen_parameters(
    data: Mapping[str, object], file: str
) -> tuple[ChargenParameters | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(_unrecognized_key_problems(data, _HEADER_KEYS | set(_CHARGEN_GROUPS), file))

    values: dict[str, object] = {}
    for group in _CHARGEN_GROUPS:
        values.update(_parse_chargen_group(data, group, file, problems))

    if problems or any(value is None for value in values.values()):
        return None, tuple(problems)
    return ChargenParameters(**values), ()
