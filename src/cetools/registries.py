"""The three shipped registries that give names meaning: characteristics,
skills, and benefit items (contracts/data-files.md).

Each `parse_*` function turns one file's already-parsed TOML dict into a
registry, collecting every problem rather than raising on the first
(research R7). The header keys `schema` and `schema-version` are accepted
here as known keys but not interpreted; the kind-and-version check itself is
`rules.py`'s job (T023), which runs before these functions are reached.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType

from cetools.errors import RulesDataError, TaskError, ValidationProblem, type_name
from cetools.notation import SkillReference

_HEADER_KEYS = frozenset({"schema", "schema-version"})

_BAND_RANGE = re.compile(r"^(\d+)-(\d+)$")
_BAND_UNBOUNDED = re.compile(r"^(\d+)\+$")


@dataclass(frozen=True, slots=True)
class Band:
    """One row of the characteristic modifier table.

    `maximum` is `None` for the sole unbounded top band, which sorts last.
    """

    minimum: int
    maximum: int | None
    dm: int


@dataclass(frozen=True, slots=True)
class CharacteristicRegistry:
    """Code (`"INT"`) to label (`"Intellect"`), in the file's order, plus
    every other fact about a characteristic FR-039 puts in data rather than
    in engine code: which class it belongs to, the modifier bands every
    score is looked up against, and the pseudo-hex symbols the profile
    renders in.
    """

    names: Mapping[str, str]
    classes: Mapping[str, str] = MappingProxyType({})
    bands: tuple[Band, ...] = ()
    pseudo_hex_minimum: int = 0
    pseudo_hex: tuple[str, ...] = ()

    def __contains__(self, code: object) -> bool:
        return code in self.names

    def characteristic_dm(self, score: int) -> int:
        if score < 0:
            raise TaskError(f"characteristic must be non-negative, got {score}")
        for band in self.bands:
            if band.minimum <= score and (band.maximum is None or score <= band.maximum):
                return band.dm
        raise RulesDataError(f"no characteristic band covers score {score}")

    def symbol(self, score: int) -> str:
        """The pseudo-hex symbol for `score` (research R13).

        Raises `RulesDataError` naming the score and the declared range when
        `score` falls outside `pseudo_hex_minimum` through
        `pseudo_hex_minimum + len(pseudo_hex) - 1`. Unreachable from the
        shipped data, whose declared range covers every score a reduction can
        floor at or a throw can produce; reachable only from an override that
        declares a shorter table.
        """
        index = score - self.pseudo_hex_minimum
        if index < 0 or index >= len(self.pseudo_hex):
            top = self.pseudo_hex_minimum + len(self.pseudo_hex) - 1
            raise RulesDataError(
                f"characteristic score {score} is outside the declared pseudo-hex range "
                f"{self.pseudo_hex_minimum}-{top}"
            )
        return self.pseudo_hex[index]

    def floor(self) -> int:
        """The value a characteristic reduction clamps at: the bottom of the
        declared pseudo-hex range, so the rules cannot produce a score the
        symbols do not cover (research R13).
        """
        return self.pseudo_hex_minimum


class SkillResolution(Enum):
    """The four distinguishable outcomes of resolving a `SkillReference`
    against a `SkillRegistry` (FR-007, contracts/notation.md).
    """

    VALID = auto()
    UNRECOGNIZED_SKILL = auto()
    SPECIALTY_NOT_ALLOWED = auto()
    UNRECOGNIZED_SPECIALTY = auto()


@dataclass(frozen=True, slots=True)
class SkillRegistry:
    """Skill name to its permitted specialties; an empty tuple means none."""

    skills: Mapping[str, tuple[str, ...]]

    def resolve(self, reference: SkillReference) -> SkillResolution:
        specialties = self.skills.get(reference.name)
        if specialties is None:
            return SkillResolution.UNRECOGNIZED_SKILL
        if reference.specialty is None:
            return SkillResolution.VALID
        if not specialties:
            return SkillResolution.SPECIALTY_NOT_ALLOWED
        if reference.specialty not in specialties:
            return SkillResolution.UNRECOGNIZED_SPECIALTY
        return SkillResolution.VALID


@dataclass(frozen=True, slots=True)
class BenefitRegistry:
    """Benefit item names, in file order."""

    items: tuple[str, ...]

    def __contains__(self, name: object) -> bool:
        return name in self.items


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


def _parse_bands(
    data: object, file: str, location: str
) -> tuple[tuple[Band, ...] | None, list[ValidationProblem]]:
    """Parse a `key -> modifier` table (`"N-M"` or `"N+"`) into bands sorted
    by `minimum`, exactly one unbounded (003-npc-generator contracts/data-files.md).

    Moved here, verbatim in shape, from the reader that used to parse
    `tasks.toml`'s `[characteristic-dms]`; the characteristics registry is
    where the bands live now (FR-039).
    """
    problems: list[ValidationProblem] = []
    if not isinstance(data, dict) or not data:
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found=(
                    "missing"
                    if data is None
                    else ("an empty table" if data == {} else type_name(data))
                ),
                expected=f"a [{location}] table with at least one entry",
            )
        )
        return None, problems

    bands: list[Band] = []
    unbounded_count = 0
    ok = True
    for key, value in data.items():
        if not isinstance(value, int) or isinstance(value, bool):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.{key}",
                    found=type_name(value),
                    expected="an integer",
                )
            )
            ok = False
            continue
        range_match = _BAND_RANGE.match(key)
        unbounded_match = _BAND_UNBOUNDED.match(key)
        if range_match:
            minimum, maximum = int(range_match.group(1)), int(range_match.group(2))
        elif unbounded_match:
            minimum, maximum = int(unbounded_match.group(1)), None
            unbounded_count += 1
        else:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.{key}",
                    found=repr(key),
                    expected="a key of the form N-M or N+",
                )
            )
            ok = False
            continue
        bands.append(Band(minimum=minimum, maximum=maximum, dm=value))

    if ok and unbounded_count != 1:
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found=f"{unbounded_count} unbounded bands",
                expected="exactly one unbounded band",
            )
        )

    if problems:
        return None, problems
    bands.sort(key=lambda band: band.minimum)
    return tuple(bands), problems


_CHARACTERISTIC_ENTRY_KEYS = frozenset({"label", "class"})


def _parse_characteristic_entry(
    code: str, entry: object, file: str
) -> tuple[str | None, str | None, list[ValidationProblem]]:
    location = f"characteristics.{code}"
    problems: list[ValidationProblem] = []
    if not isinstance(entry, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found=type_name(entry),
                expected="a table with label and class",
            )
        )
        return None, None, problems

    problems.extend(
        _unrecognized_key_problems(entry, _CHARACTERISTIC_ENTRY_KEYS, file, f"{location}.")
    )

    label = _require_nonempty_string(entry, "label", file, f"{location}.label", problems)
    characteristic_class = _require_nonempty_string(
        entry, "class", file, f"{location}.class", problems
    )
    return label, characteristic_class, problems


def _require_nonempty_string(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None:
    value = container.get(key)
    if isinstance(value, str) and value:
        return value
    found = (
        "an empty string"
        if value == ""
        else ("missing" if key not in container else type_name(value))
    )
    problems.append(
        ValidationProblem(file=file, location=location, found=found, expected="a non-empty string")
    )
    return None


def _parse_pseudo_hex(
    data: object, file: str
) -> tuple[tuple[int, tuple[str, ...]] | None, list[ValidationProblem]]:
    location = "pseudo-hex"
    problems: list[ValidationProblem] = []
    if not isinstance(data, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found="missing" if data is None else type_name(data),
                expected="a [pseudo-hex] table",
            )
        )
        return None, problems

    problems.extend(_unrecognized_key_problems(data, {"minimum", "symbols"}, file))

    minimum = data.get("minimum")
    if not isinstance(minimum, int) or isinstance(minimum, bool):
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.minimum",
                found="missing" if "minimum" not in data else type_name(minimum),
                expected="an integer",
            )
        )
        minimum = None

    symbols_raw = data.get("symbols")
    symbols: tuple[str, ...] | None = None
    if not isinstance(symbols_raw, list) or not symbols_raw:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.symbols",
                found=(
                    "missing"
                    if "symbols" not in data
                    else ("an empty array" if symbols_raw == [] else type_name(symbols_raw))
                ),
                expected="a non-empty array of strings",
            )
        )
    else:
        parsed_symbols = []
        ok = True
        for index, symbol in enumerate(symbols_raw):
            if not isinstance(symbol, str) or not symbol:
                problems.append(
                    ValidationProblem(
                        file=file,
                        location=f"{location}.symbols[{index}]",
                        found=(
                            type_name(symbol) if not isinstance(symbol, str) else "an empty string"
                        ),
                        expected="a non-empty string",
                    )
                )
                ok = False
                continue
            parsed_symbols.append(symbol)
        if ok:
            symbols = tuple(parsed_symbols)

    if minimum is None or symbols is None:
        return None, problems
    return (minimum, symbols), problems


def parse_characteristics(
    data: Mapping[str, object], file: str
) -> tuple[CharacteristicRegistry | None, tuple[ValidationProblem, ...]]:
    problems = _unrecognized_key_problems(
        data, _HEADER_KEYS | {"characteristics", "modifier-dms", "pseudo-hex"}, file
    )

    table = data.get("characteristics")
    names: dict[str, str] = {}
    classes: dict[str, str] = {}
    if not isinstance(table, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location="characteristics",
                found="missing" if table is None else type_name(table),
                expected="a [characteristics] table with at least one entry",
            )
        )
    elif not table:
        problems.append(
            ValidationProblem(
                file=file,
                location="characteristics",
                found="an empty table",
                expected="at least one entry",
            )
        )
    else:
        for code, entry in table.items():
            label, characteristic_class, entry_problems = _parse_characteristic_entry(
                code, entry, file
            )
            problems.extend(entry_problems)
            if label is not None and characteristic_class is not None:
                names[code] = label
                classes[code] = characteristic_class

    bands, band_problems = _parse_bands(data.get("modifier-dms"), file, "modifier-dms")
    problems.extend(band_problems)

    pseudo_hex, pseudo_hex_problems = _parse_pseudo_hex(data.get("pseudo-hex"), file)
    problems.extend(pseudo_hex_problems)

    if problems:
        return None, tuple(problems)
    pseudo_hex_minimum, pseudo_hex_symbols = pseudo_hex
    return (
        CharacteristicRegistry(
            names=MappingProxyType(names),
            classes=MappingProxyType(classes),
            bands=bands,
            pseudo_hex_minimum=pseudo_hex_minimum,
            pseudo_hex=pseudo_hex_symbols,
        ),
        (),
    )


def parse_skills(
    data: Mapping[str, object], file: str
) -> tuple[SkillRegistry | None, tuple[ValidationProblem, ...]]:
    problems = _unrecognized_key_problems(data, _HEADER_KEYS | {"skills"}, file)

    table = data.get("skills")
    if not isinstance(table, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location="skills",
                found="missing" if table is None else type_name(table),
                expected="a [skills] table with at least one entry",
            )
        )
        return None, tuple(problems)

    if not table:
        problems.append(
            ValidationProblem(
                file=file, location="skills", found="an empty table", expected="at least one entry"
            )
        )
        return None, tuple(problems)

    skills: dict[str, tuple[str, ...]] = {}
    for name, specialties in table.items():
        # A key carrying a specialty group can never be referenced: every
        # career entry is split into a base name and a specialty before it is
        # resolved, so `"Gun Combat (Slug Rifle)" = []` is an entry nothing
        # can reach, and a career writing that very text resolves
        # `UNRECOGNIZED_SKILL` against the base name instead. Specialties are
        # declared in the array (FR-011); a name that also spells one is a
        # mistake the author needs told about rather than a dead entry
        # (FR-006, FR-013, contracts/notation.md).
        if "(" in name or ")" in name:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"skills.{name}",
                    found=name,
                    expected=(
                        "a skill name with no parentheses: a specialty is declared in this "
                        "skill's array, never spelled into its name"
                    ),
                )
            )
            continue
        if not isinstance(specialties, list):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"skills.{name}",
                    found=type_name(specialties),
                    expected="an array of strings",
                )
            )
            continue
        # Every offending element, not the first: reporting one made this the
        # one field in the feature where fixing the reported mistake revealed
        # the next on the following run, which FR-021's collect-everything and
        # SC-003's "the number of runs needed to find every problem in a file
        # is always one" forbid. Both sibling parsers below already loop.
        bad = [
            ValidationProblem(
                file=file,
                location=f"skills.{name}[{index}]",
                found=type_name(specialty),
                expected="a string",
            )
            for index, specialty in enumerate(specialties)
            if not isinstance(specialty, str)
        ]
        if bad:
            problems.extend(bad)
            continue
        skills[name] = tuple(specialties)

    if problems:
        return None, tuple(problems)
    return SkillRegistry(skills=MappingProxyType(skills)), ()


def parse_benefits(
    data: Mapping[str, object], file: str
) -> tuple[BenefitRegistry | None, tuple[ValidationProblem, ...]]:
    problems = _unrecognized_key_problems(data, _HEADER_KEYS | {"benefits"}, file)

    items = data.get("benefits")
    if not isinstance(items, list):
        problems.append(
            ValidationProblem(
                file=file,
                location="benefits",
                found="missing" if items is None else type_name(items),
                expected="an array of strings with at least one entry",
            )
        )
        return None, tuple(problems)

    if not items:
        problems.append(
            ValidationProblem(
                file=file,
                location="benefits",
                found="an empty array",
                expected="at least one entry",
            )
        )
        return None, tuple(problems)

    names: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"benefits[{index}]",
                    found=type_name(item),
                    expected="a string",
                )
            )
            continue
        names.append(item)

    if problems:
        return None, tuple(problems)
    return BenefitRegistry(items=tuple(names)), ()
