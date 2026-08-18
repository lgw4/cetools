"""The three shipped registries that give names meaning: characteristics,
skills, and benefit items (contracts/data-files.md).

Each `parse_*` function turns one file's already-parsed TOML dict into a
registry, collecting every problem rather than raising on the first
(research R7). The header keys `schema` and `schema-version` are accepted
here as known keys but not interpreted; the kind-and-version check itself is
`rules.py`'s job (T023), which runs before these functions are reached.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType

from cetools.errors import ValidationProblem, type_name
from cetools.notation import SkillReference

_HEADER_KEYS = frozenset({"schema", "schema-version"})


@dataclass(frozen=True, slots=True)
class CharacteristicRegistry:
    """Code (`"INT"`) to label (`"Intellect"`), in the file's order."""

    names: Mapping[str, str]

    def __contains__(self, code: object) -> bool:
        return code in self.names


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
    data: Mapping[str, object], allowed: frozenset[str], file: str
) -> list[ValidationProblem]:
    extra = sorted(set(data) - allowed)
    return [
        ValidationProblem(
            file=file,
            location=key,
            found=f"unrecognized key {key!r}",
            expected=f"one of: {', '.join(sorted(allowed))}",
        )
        for key in extra
    ]


def parse_characteristics(
    data: Mapping[str, object], file: str
) -> tuple[CharacteristicRegistry | None, tuple[ValidationProblem, ...]]:
    problems = _unrecognized_key_problems(data, _HEADER_KEYS | {"characteristics"}, file)

    table = data.get("characteristics")
    if not isinstance(table, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location="characteristics",
                found="missing" if table is None else type_name(table),
                expected="a [characteristics] table with at least one entry",
            )
        )
        return None, tuple(problems)

    if not table:
        problems.append(
            ValidationProblem(
                file=file,
                location="characteristics",
                found="an empty table",
                expected="at least one entry",
            )
        )
        return None, tuple(problems)

    names: dict[str, str] = {}
    for code, label in table.items():
        if not isinstance(label, str):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"characteristics.{code}",
                    found=type_name(label),
                    expected="a string",
                )
            )
            continue
        names[code] = label

    if problems:
        return None, tuple(problems)
    return CharacteristicRegistry(names=MappingProxyType(names)), ()


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
