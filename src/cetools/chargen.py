"""The universal chargen tables: draft, aging, mishaps, background skills,
medical tiers, and the parameters the walk reads everything else from
(contracts/data-files.md, data-model.md).

Each `parse_*` function turns one file's already-parsed TOML dict into a
table, collecting every problem rather than raising on the first, following
the convention `registries.py` and `careers.py` established.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from cetools.errors import RulesDataError, ValidationProblem, type_name
from cetools.tasks import _check_dice

_HEADER_KEYS = frozenset({"schema", "schema-version"})


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
