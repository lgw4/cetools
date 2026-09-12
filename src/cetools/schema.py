"""The shared field-checking vocabulary for rules-data TOML files
(contracts/schema-vocabulary.md, 006-validation-vocabulary;
contracts/parse-context.md, 007-parse-context-carrier).

Package-internal: nothing outside `cetools` is expected to import this
module (FR-016). The five parsers -- `rules.py`, `careers.py`,
`registries.py`, `names.py`, `chargen.py` -- each hand-rolled these same
eight checks; this module gives the checking layer the one home
`errors.type_name` already gives the vocabulary built on it, reached
through `ParseContext`, the carrier each parser descends a file with.
"""

from collections.abc import Mapping

from cetools.errors import RulesDataError, ValidationProblem, type_name
from cetools.tasks import _check_dice

HEADER_KEYS = frozenset({"schema", "schema-version"})


class ParseContext:
    """The file, the location, and the shared problem collection a rules-data
    parser carries by hand today, bundled into one object
    (contracts/parse-context.md, 007-parse-context-carrier).

    `file` and `location` are set once and never reassigned: descent (`at`)
    derives a new carrier rather than mutating the one it is called on. That is
    a convention the parsers keep, not something this class enforces -- both
    attributes are plain and writable, and nothing here would stop a caller
    rebinding them. The problem collection is the deliberate exception: it is
    shared by reference with every derived carrier and is appended to, which is
    what makes a problem recorded at any depth reach the one list the loader
    reports from (FR-004).

    The watermark -- the collection's length when this carrier was constructed
    -- is private and is what `failed` measures against, making every carrier
    its own scope (research R4).
    """

    def __init__(
        self,
        file: str,
        location: str = "",
        problems: list[ValidationProblem] | None = None,
    ) -> None:
        self.file = file
        self.location = location
        self._problems = problems if problems is not None else []
        self._watermark = len(self._problems)

    def at(self, *parts: str | int) -> "ParseContext":
        location = self.location
        for part in parts:
            if isinstance(part, int):
                location = f"{location}[{part}]"
            elif location:
                location = f"{location}.{part}"
            else:
                location = part
        return ParseContext(self.file, location, self._problems)

    def report(self, *, found: str, expected: str) -> None:
        self._problems.append(
            ValidationProblem(
                file=self.file, location=self.location, found=found, expected=expected
            )
        )

    @property
    def problems(self) -> tuple[ValidationProblem, ...]:
        return tuple(self._problems)

    @property
    def failed(self) -> bool:
        return len(self._problems) > self._watermark

    def require_int(
        self, container: Mapping[str, object], key: str, *, minimum: int | None = None
    ) -> int | None:
        location = self.at(key).location
        if key not in container:
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found="missing", expected="an integer"
                )
            )
            return None
        value = container[key]
        if not isinstance(value, int) or isinstance(value, bool):
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=location,
                    found=type_name(value),
                    expected="an integer",
                )
            )
            return None
        if minimum is not None and value < minimum:
            expected = "a positive integer" if minimum == 1 else f"an integer >= {minimum}"
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found=str(value), expected=expected
                )
            )
            return None
        return value

    def require_string(self, container: Mapping[str, object], key: str) -> str | None:
        location = self.at(key).location
        if key not in container:
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=location,
                    found="missing",
                    expected="a non-empty string",
                )
            )
            return None
        value = container[key]
        if not isinstance(value, str) or not value:
            found = type_name(value) if not isinstance(value, str) else "an empty string"
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found=found, expected="a non-empty string"
                )
            )
            return None
        return value

    def require_bool(self, container: Mapping[str, object], key: str) -> bool | None:
        location = self.at(key).location
        if key not in container:
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found="missing", expected="a boolean"
                )
            )
            return None
        value = container[key]
        if not isinstance(value, bool):
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=location,
                    found=type_name(value),
                    expected="a boolean",
                )
            )
            return None
        return value

    def require_roll(self, container: Mapping[str, object], key: str) -> str | None:
        """A dice-notation field, rejecting `d66`: the row a table reads is a
        throw's total, and `d66` composes two faces into a two-digit table
        value rather than describing a count and a side count
        (001-dice-task-engine FR-029).
        """
        location = self.at(key).location
        if key not in container:
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found="missing", expected="a string"
                )
            )
            return None
        value = container[key]
        if not isinstance(value, str):
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found=type_name(value), expected="a string"
                )
            )
            return None
        try:
            _check_dice(value)
        except RulesDataError as exc:
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found=repr(value), expected=str(exc)
                )
            )
            return None
        return value

    def require_dict(self, value: object, *, expected: str) -> dict | None:
        if not isinstance(value, dict):
            found = "missing" if value is None else type_name(value)
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=self.location, found=found, expected=expected
                )
            )
            return None
        return value

    def optional_bool(
        self, container: Mapping[str, object], key: str, *, default: bool = False
    ) -> bool:
        if key not in container:
            return default
        value = container[key]
        if not isinstance(value, bool):
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=self.at(key).location,
                    found=type_name(value),
                    expected="a boolean",
                )
            )
            return default
        return value

    def unrecognized_keys(
        self, data: Mapping[str, object], allowed: frozenset[str] | set[str]
    ) -> None:
        allowed = frozenset(allowed)
        for key in sorted(set(data) - allowed):
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=self.at(key).location,
                    found=f"unrecognized key {key!r}",
                    expected=f"one of: {', '.join(sorted(allowed))}",
                )
            )

    def require_list(
        self,
        container: Mapping[str, object],
        key: str,
        *,
        expected: str,
        expected_missing: str | None = None,
        expected_empty: str | None = None,
        allow_empty: bool = False,
    ) -> list | None:
        location = self.at(key).location
        if key not in container:
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=location,
                    found="missing",
                    expected=expected_missing if expected_missing is not None else expected,
                )
            )
            return None
        value = container[key]
        if not isinstance(value, list):
            self._problems.append(
                ValidationProblem(
                    file=self.file, location=location, found=type_name(value), expected=expected
                )
            )
            return None
        if not value and not allow_empty:
            self._problems.append(
                ValidationProblem(
                    file=self.file,
                    location=location,
                    found="an empty array",
                    expected=expected_empty if expected_empty is not None else expected,
                )
            )
            return None
        return value
