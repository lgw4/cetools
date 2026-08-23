"""The `npc` JSON payload (contracts/json-output.md). One shape whatever
the count (FR-050a): every field present unconditionally, every seed a
string, key order pinned throughout.
"""

import dataclasses
import json
from importlib.metadata import version

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
from cetools.render import as_dict, as_json, as_text
from cetools.tasks import Modifier

_VERSION = version("cetools")
_PACKAGED_PROVENANCE = Provenance(version=_VERSION, files=(), ignored=())

_CHARACTER = Character(
    seed=14333185781139156525,
    name="Amara Okonkwo",
    given_name="Amara",
    surname="Okonkwo",
    surname_region="Africa",
    title="Lieutenant",
    characteristics={"STR": 9, "DEX": 10, "END": 7, "INT": 11, "EDU": 8, "SOC": 6},
    characteristic_symbols=("9", "A", "7", "B", "8", "6"),
    skills=(
        CharacterSkill(name="Comms", specialty=None, level=1),
        CharacterSkill(name="Gun Combat", specialty="Slug Rifle", level=1),
        CharacterSkill(name="Leadership", specialty=None, level=0),
    ),
    careers=(
        CareerService(
            career="Navy",
            terms=4,
            ladder="officer",
            rank=2,
            title="Lieutenant",
            commissioned=True,
            entered_by="selected",
            ended="re-enlistment",
            benefit_rolls=4,
        ),
    ),
    age=34,
    funds=55000,
    debt=12000,
    pension=0,
    benefits=("High Passage", "High Passage", "Weapon"),
    history=(
        HistoryStep(
            kind="qualification",
            career="Navy",
            term=1,
            throw=StepThrow(
                faces=(2, 5),
                modifiers=(Modifier(label="Characteristic 11", value=1),),
                total=8,
                target=6,
                success=True,
            ),
            selected="",
            effects=(),
        ),
        HistoryStep(
            kind="rank-bonus",
            career="Navy",
            term=1,
            throw=None,
            selected="",
            effects=(StepEffect(kind="skill", subject="Zero-G", amount=1),),
        ),
    ),
)

_BATCH = CharacterBatch(
    seed=14333185781139156525, provenance=_PACKAGED_PROVENANCE, characters=(_CHARACTER,)
)


def test_top_level_key_order():
    assert list(as_dict(_BATCH)) == ["kind", "seed", "provenance", "characters"]


def test_top_level_kind_is_npc():
    assert as_dict(_BATCH)["kind"] == "npc"


def test_master_seed_is_a_string():
    payload = as_dict(_BATCH)
    assert payload["seed"] == "14333185781139156525"
    assert isinstance(payload["seed"], str)


def test_provenance_is_the_existing_shape():
    payload = as_dict(_BATCH)
    assert list(payload["provenance"]) == ["source", "version", "files", "ignored"]
    assert payload["provenance"]["version"] == _VERSION


def test_character_key_order():
    character = as_dict(_BATCH)["characters"][0]
    assert list(character) == [
        "seed",
        "name",
        "given_name",
        "surname",
        "surname_region",
        "title",
        "characteristics",
        "characteristic_symbols",
        "skills",
        "careers",
        "age",
        "funds",
        "debt",
        "pension",
        "benefits",
        "history",
    ]


def test_a_characters_own_seed_is_a_string_and_at_position_0_equals_the_master():
    character = as_dict(_BATCH)["characters"][0]
    assert character["seed"] == "14333185781139156525"
    assert character["seed"] == as_dict(_BATCH)["seed"]


def test_every_produced_types_dict_keys_match_its_dataclass_fields():
    # T184: `characteristic_symbols` was added to `Character` (T159) and
    # never reached `as_dict` — the only field-versus-emitted mismatch
    # across all six produced types, the other five agreeing exactly. This
    # guard is what would have caught it.
    character = as_dict(_BATCH)["characters"][0]
    assert set(character) == {f.name for f in dataclasses.fields(Character)}
    assert set(character["skills"][0]) == {f.name for f in dataclasses.fields(CharacterSkill)}
    assert set(character["careers"][0]) == {f.name for f in dataclasses.fields(CareerService)}
    assert set(character["history"][0]) == {f.name for f in dataclasses.fields(HistoryStep)}
    assert set(character["history"][0]["throw"]) == {f.name for f in dataclasses.fields(StepThrow)}
    assert set(character["history"][1]["effects"][0]) == {
        f.name for f in dataclasses.fields(StepEffect)
    }


def test_skill_key_order():
    skill = as_dict(_BATCH)["characters"][0]["skills"][0]
    assert list(skill) == ["name", "specialty", "level"]


def test_specialty_is_null_never_empty_string():
    skills = as_dict(_BATCH)["characters"][0]["skills"]
    parents = [skill for skill in skills if skill["name"] in ("Comms", "Leadership")]
    assert parents
    for skill in parents:
        assert skill["specialty"] is None


def test_skills_are_sorted_the_way_the_sheet_sorts_them():
    # Compared against the sheet itself, not against an independently sorted
    # copy of the JSON names: a case where the label alone and the rendered
    # "label-level" string disagree on order (T154, contracts/cli.md's "over
    # the rendered name-and-specialty") would pass a self-referential
    # `sorted(names, key=str.casefold)` check while actually disagreeing
    # with `as_text`.
    sheet_line3 = as_text(_CHARACTER).split("\n")[2]
    sheet_labels = [entry.rsplit("-", 1)[0] for entry in sheet_line3.split(", ")]
    json_labels = [
        skill["name"] if skill["specialty"] is None else f"{skill['name']} ({skill['specialty']})"
        for skill in as_dict(_BATCH)["characters"][0]["skills"]
    ]
    assert json_labels == sheet_labels


def test_career_service_key_order():
    career = as_dict(_BATCH)["characters"][0]["careers"][0]
    assert list(career) == [
        "career",
        "terms",
        "ladder",
        "rank",
        "title",
        "commissioned",
        "entered_by",
        "ended",
        "benefit_rolls",
    ]


def test_history_step_key_order():
    step = as_dict(_BATCH)["characters"][0]["history"][0]
    assert list(step) == ["kind", "career", "term", "throw", "selected", "effects"]


def test_throw_key_order():
    step = as_dict(_BATCH)["characters"][0]["history"][0]
    assert list(step["throw"]) == ["faces", "modifiers", "total", "target", "success"]


def test_throw_is_null_for_a_step_that_decided_rather_than_threw():
    step = as_dict(_BATCH)["characters"][0]["history"][1]
    assert step["throw"] is None


def test_effect_key_order():
    step = as_dict(_BATCH)["characters"][0]["history"][1]
    assert list(step["effects"][0]) == ["kind", "subject", "amount"]


def test_every_key_present_unconditionally_for_a_supplied_name_and_empty_benefits():
    supplied = dataclasses.replace(
        _CHARACTER, given_name="", surname="", surname_region="", benefits=()
    )
    payload = as_dict(supplied)
    assert payload["given_name"] == ""
    assert payload["surname"] == ""
    assert payload["surname_region"] == ""
    assert payload["benefits"] == []
    assert payload["pension"] == 0


def test_json_is_indent_two_with_a_trailing_newline():
    text = as_json(_BATCH)
    assert text.endswith("}\n")
    assert '\n  "kind": "npc"' in text


def test_non_ascii_names_are_emitted_as_themselves():
    named = dataclasses.replace(_CHARACTER, name="Amara Ökonkwo")
    batch = dataclasses.replace(_BATCH, characters=(named,))
    text = as_json(batch)
    assert "Ökonkwo" in text
    assert "\\u00d6" not in text
    assert json.loads(text)["characters"][0]["name"] == "Amara Ökonkwo"


def test_payload_is_json_serializable_round_trip():
    payload = as_dict(_BATCH)
    assert json.loads(json.dumps(payload)) == payload


# --- T116 ---


def test_batch_and_single_character_dicts_agree():
    payload = as_dict(_BATCH)
    for i, character in enumerate(_BATCH.characters):
        assert payload["characters"][i] == as_dict(character)


def test_every_throw_total_equals_sum_of_faces_plus_modifier_values():
    for step in _CHARACTER.history:
        if step.throw is not None:
            expected = sum(step.throw.faces) + sum(m.value for m in step.throw.modifiers)
            assert step.throw.total == expected


def test_every_generated_throw_total_equals_sum_of_faces_plus_modifier_values():
    # T196: the case above iterates `_CHARACTER.history`, a hand-constructed
    # fixture whose every `StepThrow` was authored to already satisfy the
    # invariant — so the contract's own stated assertion had never once run
    # against a walk the generator actually produced. The aging total
    # (`sum(faces) + roll_modifier - total_terms_served`) and the
    # medical-bill total (`sum(faces) + roll_modifier + rank_bonus`) both
    # applied a modifier to `total` while recording an empty `modifiers`
    # tuple, which only a generated character's history could catch.
    from cetools.dice import Roller
    from cetools.generator import generate_character
    from cetools.rules import load_rules

    rules = load_rules()
    checked = 0
    for seed in range(300):
        character = generate_character(Roller(seed), rules)
        for step in character.history:
            if step.throw is None:
                continue
            checked += 1
            expected = sum(step.throw.faces) + sum(m.value for m in step.throw.modifiers)
            assert step.throw.total == expected, (seed, step.kind)
    assert checked


# --- T177 ---


def test_a_multi_character_run_matches_the_same_document_shape_as_one():
    # SC-010 and FR-050a: "a run of one character and a run of twelve emit
    # the same document shape, verified by checking both against one
    # contract." Every check above runs against `_BATCH`, which holds
    # exactly one character, so that half of the criterion was verified by
    # nothing. Three distinct characters here, checked against the same
    # key orders `_BATCH`'s single character is checked against elsewhere
    # in this file.
    second = dataclasses.replace(_CHARACTER, seed=1, name="Kenji Sato")
    third = dataclasses.replace(_CHARACTER, seed=2, name="Priya Nair")
    multi_batch = CharacterBatch(
        seed=_BATCH.seed, provenance=_PACKAGED_PROVENANCE, characters=(_CHARACTER, second, third)
    )
    payload = as_dict(multi_batch)
    assert len(payload["characters"]) == 3

    for i, character_obj in enumerate(multi_batch.characters):
        character = payload["characters"][i]
        assert character == as_dict(character_obj)
        assert list(character) == [
            "seed",
            "name",
            "given_name",
            "surname",
            "surname_region",
            "title",
            "characteristics",
            "characteristic_symbols",
            "skills",
            "careers",
            "age",
            "funds",
            "debt",
            "pension",
            "benefits",
            "history",
        ]
        assert list(character["skills"][0]) == ["name", "specialty", "level"]
        assert list(character["careers"][0]) == [
            "career",
            "terms",
            "ladder",
            "rank",
            "title",
            "commissioned",
            "entered_by",
            "ended",
            "benefit_rolls",
        ]
        assert list(character["history"][0]) == [
            "kind",
            "career",
            "term",
            "throw",
            "selected",
            "effects",
        ]
        assert list(character["history"][0]["throw"]) == [
            "faces",
            "modifiers",
            "total",
            "target",
            "success",
        ]
        assert list(character["history"][1]["effects"][0]) == ["kind", "subject", "amount"]
