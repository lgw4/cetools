"""The produced value: a fully lived character and its generation history
(contracts/library-api.md, data-model.md).

Unlike the schema modules, nothing here parses TOML. `generate_character`
constructs these directly, and the shapes exist so a caller can address any
part of a character or its history without re-deriving it from rendered
text.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from cetools.provenance import Provenance
from cetools.tasks import Modifier

# Closed (data-model.md "The generation history"): a misspelled kind is a
# new kind rather than a typo, and SC-005's automated traceability check
# groups by it. Enforced here, not left to convention, because a twelfth
# `StepEffect` kind would be the chain running past the numbers on the
# sheet (FR-028).
_HISTORY_STEP_KINDS = frozenset(
    {
        "characteristics",
        "background-skills",
        "career-selected",
        "qualification",
        "draft",
        "career-entered",
        "basic-training",
        "rank-bonus",
        "survival",
        "mishap",
        "injury",
        "commission",
        "advancement",
        "skill-roll",
        "aging",
        "continuation",
        "re-enlistment",
        "career-ended",
        "mustering-out",
        "benefit",
        "medical-bills",
        "debt-settled",
        "pension",
    }
)

_STEP_EFFECT_KINDS = frozenset(
    {
        "characteristic",
        "skill",
        "credits",
        "benefit",
        "debt",
        "pension",
        "age",
        "rank",
        "commission",
        "career",
        "benefit-roll-forfeit",
    }
)


@dataclass(frozen=True, slots=True)
class StepThrow:
    """One throw in the lifepath, lighter than `tasks.CheckResult`: no
    provenance, so a character does not carry the provenance of its own
    rules data once per throw.

    A table-reading throw, where there is no target to beat, carries
    `target = 0` and `success = True`; the row it read is in the owning
    `HistoryStep.selected`.
    """

    faces: tuple[int, ...]
    modifiers: tuple[Modifier, ...]
    total: int
    target: int
    success: bool


@dataclass(frozen=True, slots=True)
class StepEffect:
    """One consequence of a history step. `amount` means nothing for
    `commission`, and is `0` there.
    """

    kind: str
    subject: str
    amount: int

    def __post_init__(self) -> None:
        if self.kind not in _STEP_EFFECT_KINDS:
            raise ValueError(f"unrecognized step effect kind: {self.kind!r}")


@dataclass(frozen=True, slots=True)
class HistoryStep:
    """One step of the lifepath walk. `career` is `""` and `term` is `0`
    where the step falls outside a career or a term.
    """

    kind: str
    career: str
    term: int
    throw: StepThrow | None
    selected: str
    effects: tuple[StepEffect, ...]

    def __post_init__(self) -> None:
        if self.kind not in _HISTORY_STEP_KINDS:
            raise ValueError(f"unrecognized history step kind: {self.kind!r}")


@dataclass(frozen=True, slots=True)
class CharacterSkill:
    """A fact about a person, not an instruction written in a table —
    deliberately not `notation.SkillGrant`, which has the same shape.
    """

    name: str
    specialty: str | None
    level: int


@dataclass(frozen=True, slots=True)
class CareerService:
    """One career entered and ended. `entered_by` and `ended` are also
    history steps, carried here too so SC-004's audit reads the character's
    own fields rather than reconstructing each service by scanning the
    history for its boundaries.
    """

    career: str
    terms: int
    ladder: str
    rank: int
    title: str
    commissioned: bool
    entered_by: str
    ended: str
    benefit_rolls: int


@dataclass(frozen=True, slots=True)
class Character:
    """A fully lived character. Always alive, always named, always
    internally consistent (FR-022, FR-023, SC-003).
    """

    seed: int
    name: str
    given_name: str
    surname: str
    surname_region: str
    title: str
    characteristics: Mapping[str, int]
    skills: tuple[CharacterSkill, ...]
    careers: tuple[CareerService, ...]
    age: int
    funds: int
    debt: int
    pension: int
    benefits: tuple[str, ...]
    history: tuple[HistoryStep, ...]


@dataclass(frozen=True, slots=True)
class CharacterBatch:
    """`count` characters generated from one master seed. Position 0's
    character carries the same seed as `seed` itself (research R2).
    """

    seed: int
    provenance: Provenance
    characters: tuple[Character, ...]
