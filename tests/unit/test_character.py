"""The seven produced-value types (contracts/library-api.md, data-model.md).

Nothing here parses TOML: these are constructed directly by the walk, so
these tests exercise construction and the two closed `kind` sets rather than
a parser.
"""

import dataclasses

import pytest

from cetools.character import (
    CareerService,
    Character,
    CharacterBatch,
    CharacterSkill,
    HistoryStep,
    StepEffect,
    StepThrow,
)
from cetools.provenance import Provenance
from cetools.tasks import Modifier


def _field_names(cls) -> tuple[str, ...]:
    return tuple(f.name for f in dataclasses.fields(cls))


def _is_frozen_and_slotted(cls) -> bool:
    return cls.__dataclass_params__.frozen and bool(cls.__slots__)


class TestFieldShapes:
    def test_step_throw_fields_in_contract_order(self):
        assert _field_names(StepThrow) == ("faces", "modifiers", "total", "target", "success")
        assert _is_frozen_and_slotted(StepThrow)

    def test_step_effect_fields_in_contract_order(self):
        assert _field_names(StepEffect) == ("kind", "subject", "amount")
        assert _is_frozen_and_slotted(StepEffect)

    def test_history_step_fields_in_contract_order(self):
        assert _field_names(HistoryStep) == (
            "kind",
            "career",
            "term",
            "throw",
            "selected",
            "effects",
        )
        assert _is_frozen_and_slotted(HistoryStep)

    def test_character_skill_fields_in_contract_order(self):
        assert _field_names(CharacterSkill) == ("name", "specialty", "level")
        assert _is_frozen_and_slotted(CharacterSkill)

    def test_career_service_fields_in_contract_order(self):
        assert _field_names(CareerService) == (
            "career",
            "terms",
            "ladder",
            "rank",
            "title",
            "commissioned",
            "entered_by",
            "ended",
            "benefit_rolls",
        )
        assert _is_frozen_and_slotted(CareerService)

    def test_character_fields_in_contract_order(self):
        assert _field_names(Character) == (
            "seed",
            "name",
            "given_name",
            "surname",
            "surname_region",
            "title",
            "characteristics",
            "skills",
            "careers",
            "age",
            "funds",
            "debt",
            "pension",
            "benefits",
            "history",
        )
        assert _is_frozen_and_slotted(Character)

    def test_character_batch_fields_in_contract_order(self):
        assert _field_names(CharacterBatch) == ("seed", "provenance", "characters")
        assert _is_frozen_and_slotted(CharacterBatch)


def _throw(**overrides) -> StepThrow:
    fields = dict(
        faces=(4, 5), modifiers=(Modifier(label="EDU", value=1),), total=10, target=8, success=True
    )
    fields.update(overrides)
    return StepThrow(**fields)


class TestStepThrow:
    def test_total_is_sum_of_faces_plus_modifiers(self):
        throw = _throw(faces=(3, 4), modifiers=(Modifier(label="DEX", value=2),), total=9)
        assert throw.total == sum(throw.faces) + sum(m.value for m in throw.modifiers)

    def test_a_table_reading_throw_carries_target_zero_and_success_true(self):
        throw = _throw(faces=(4,), modifiers=(), total=4, target=0, success=True)
        assert throw.target == 0
        assert throw.success is True


class TestStepEffectClosedKind:
    @pytest.mark.parametrize(
        "kind",
        [
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
        ],
    )
    def test_every_closed_kind_constructs(self, kind):
        StepEffect(kind=kind, subject="STR", amount=0)

    def test_an_unrecognized_kind_raises(self):
        with pytest.raises(ValueError):
            StepEffect(kind="nonexistent-kind", subject="", amount=0)


class TestHistoryStepClosedKind:
    @pytest.mark.parametrize(
        "kind",
        [
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
        ],
    )
    def test_every_closed_kind_constructs(self, kind):
        HistoryStep(kind=kind, career="", term=0, throw=None, selected="", effects=())

    def test_an_unrecognized_kind_raises(self):
        with pytest.raises(ValueError):
            HistoryStep(
                kind="nonexistent-kind", career="", term=0, throw=None, selected="", effects=()
            )

    def test_a_step_that_decided_rather_than_threw_carries_no_throw(self):
        step = HistoryStep(
            kind="career-selected", career="", term=0, throw=None, selected="Navy", effects=()
        )
        assert step.throw is None
        assert step.selected == "Navy"


def _character(**overrides) -> Character:
    fields = dict(
        seed=1,
        name="Alex Smith",
        given_name="Alex",
        surname="Smith",
        surname_region="Europe",
        title="",
        characteristics={"STR": 7},
        skills=(CharacterSkill(name="Gun Combat", specialty=None, level=0),),
        careers=(
            CareerService(
                career="Navy",
                terms=1,
                ladder="enlisted",
                rank=0,
                title="Starman",
                commissioned=False,
                entered_by="selected",
                ended="term cap",
                benefit_rolls=1,
            ),
        ),
        age=22,
        funds=1000,
        debt=0,
        pension=0,
        benefits=("Weapon",),
        history=(
            HistoryStep(
                kind="characteristics", career="", term=0, throw=None, selected="", effects=()
            ),
        ),
    )
    fields.update(overrides)
    return Character(**fields)


class TestCharacter:
    def test_constructs_from_every_field(self):
        character = _character()
        assert character.name == "Alex Smith"
        assert character.funds >= 0
        assert character.debt >= 0

    def test_a_supplied_name_leaves_given_name_and_surname_empty(self):
        character = _character(given_name="", surname="", surname_region="")
        assert character.given_name == ""
        assert character.surname == ""
        assert character.surname_region == ""


class TestCharacterBatch:
    def test_constructs_from_every_field(self):
        batch = CharacterBatch(
            seed=1,
            provenance=Provenance(version="test", files=(), ignored=()),
            characters=(_character(),),
        )
        assert batch.seed == 1
        assert len(batch.characters) == 1
