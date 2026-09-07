"""The shared field-checking vocabulary for rules-data TOML files
(contracts/schema-vocabulary.md, 006-validation-vocabulary).

Package-internal: nothing outside `cetools` is expected to import this
module (FR-016). The five parsers -- `rules.py`, `careers.py`,
`registries.py`, `names.py`, `chargen.py` -- each hand-rolled these same
seven checks; this module gives the checking layer the one home
`errors.type_name` already gives the vocabulary built on it.
"""

from collections.abc import Mapping

from cetools.errors import RulesDataError, ValidationProblem, type_name
from cetools.tasks import _check_dice


def require_int(
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
        expected = "a positive integer" if minimum == 1 else f"an integer >= {minimum}"
        problems.append(
            ValidationProblem(file=file, location=location, found=str(value), expected=expected)
        )
        return None
    return value


def require_string(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None:
    if key not in container:
        problems.append(
            ValidationProblem(
                file=file, location=location, found="missing", expected="a non-empty string"
            )
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


def require_bool(
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


def require_roll(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None:
    """A dice-notation field, rejecting `d66`: the row a table reads is a
    throw's total, and `d66` composes two faces into a two-digit table value
    rather than describing a count and a side count (001-dice-task-engine
    FR-029).
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


def require_dict(
    value: object, file: str, location: str, expected: str, problems: list[ValidationProblem]
) -> dict | None:
    if not isinstance(value, dict):
        found = "missing" if value is None else type_name(value)
        problems.append(
            ValidationProblem(file=file, location=location, found=found, expected=expected)
        )
        return None
    return value


def optional_bool(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
    *,
    default: bool = False,
) -> bool:
    if key not in container:
        return default
    value = container[key]
    if not isinstance(value, bool):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a boolean"
            )
        )
        return default
    return value


def unrecognized_key_problems(
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
