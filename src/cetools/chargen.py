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

from cetools.errors import RulesDataError, ValidationProblem, type_name
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
