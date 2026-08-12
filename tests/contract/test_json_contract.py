import json

from cetools.dice import ThrowResult
from cetools.render import as_dict
from cetools.tasks import CheckResult, Modifier

_ROLL = ThrowResult(
    notation="2d6+1",
    faces=(1, 5),
    modifier=1,
    total=7,
    seed=14333185781139156525,
)

_D66 = ThrowResult(
    notation="d66",
    faces=(1, 5),
    modifier=0,
    total=15,
    seed=14333185781139156525,
)

_CHECK = CheckResult(
    faces=(1, 5),
    dice_total=6,
    modifiers=(
        Modifier(label="Difficulty (Difficult)", value=-2),
        Modifier(label="Characteristic 9", value=1),
        Modifier(label="Skill 2", value=2),
        Modifier(label="cover", value=-2),
    ),
    total=5,
    target=8,
    success=False,
    seed=14333185781139156525,
)


def test_roll_payload_key_set_and_order_matches_contract():
    payload = as_dict(_ROLL)
    assert list(payload) == ["kind", "notation", "faces", "modifier", "total", "seed"]


def test_roll_payload_kind_is_roll():
    assert as_dict(_ROLL)["kind"] == "roll"


def test_roll_payload_value_types():
    payload = as_dict(_ROLL)
    assert isinstance(payload["notation"], str)
    assert isinstance(payload["faces"], list)
    assert all(isinstance(face, int) for face in payload["faces"])
    assert isinstance(payload["modifier"], int)
    assert isinstance(payload["total"], int)
    assert isinstance(payload["seed"], str)


def test_roll_payload_matches_contract_example():
    assert as_dict(_ROLL) == {
        "kind": "roll",
        "notation": "2d6+1",
        "faces": [1, 5],
        "modifier": 1,
        "total": 7,
        "seed": "14333185781139156525",
    }


def test_roll_payload_arithmetic_invariant():
    payload = as_dict(_ROLL)
    assert payload["total"] == sum(payload["faces"]) + payload["modifier"]


def test_d66_payload_matches_contract_example():
    assert as_dict(_D66) == {
        "kind": "roll",
        "notation": "d66",
        "faces": [1, 5],
        "modifier": 0,
        "total": 15,
        "seed": "14333185781139156525",
    }


def test_check_payload_key_set_and_order_matches_contract():
    payload = as_dict(_CHECK)
    assert list(payload) == [
        "kind",
        "faces",
        "dice_total",
        "modifiers",
        "total",
        "target",
        "success",
        "seed",
    ]


def test_check_payload_kind_is_check():
    assert as_dict(_CHECK)["kind"] == "check"


def test_check_payload_value_types():
    payload = as_dict(_CHECK)
    assert isinstance(payload["faces"], list)
    assert all(isinstance(face, int) for face in payload["faces"])
    assert isinstance(payload["dice_total"], int)
    assert isinstance(payload["modifiers"], list)
    for modifier in payload["modifiers"]:
        assert list(modifier) == ["label", "value"]
        assert isinstance(modifier["label"], str)
        assert isinstance(modifier["value"], int)
    assert isinstance(payload["total"], int)
    assert isinstance(payload["target"], int)
    assert isinstance(payload["success"], bool)
    assert isinstance(payload["seed"], str)


def test_check_payload_matches_contract_example():
    assert as_dict(_CHECK) == {
        "kind": "check",
        "faces": [1, 5],
        "dice_total": 6,
        "modifiers": [
            {"label": "Difficulty (Difficult)", "value": -2},
            {"label": "Characteristic 9", "value": 1},
            {"label": "Skill 2", "value": 2},
            {"label": "cover", "value": -2},
        ],
        "total": 5,
        "target": 8,
        "success": False,
        "seed": "14333185781139156525",
    }


def test_check_payload_total_arithmetic_invariant():
    payload = as_dict(_CHECK)
    assert payload["total"] == payload["dice_total"] + sum(
        m["value"] for m in payload["modifiers"]
    )


def test_check_payload_success_invariant():
    payload = as_dict(_CHECK)
    assert payload["success"] == (payload["total"] >= payload["target"])


def test_seed_type_is_str_not_int():
    payload = as_dict(_ROLL)
    assert isinstance(payload["seed"], str)
    assert not isinstance(payload["seed"], bool)
    assert type(payload["seed"]) is str, "seed must stay a JSON string; do not tidy to int"


def test_payloads_are_json_serializable_round_trip():
    for result in (_ROLL, _D66, _CHECK):
        payload = as_dict(result)
        assert json.loads(json.dumps(payload)) == payload
