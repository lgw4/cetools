from cetools.engine.models import GenerationFailure, characteristic_modifier
from cetools.engine.pseudohex import encode_upp

MODIFIER_TABLE = [
    (0, -2),
    (1, -2),
    (2, -2),
    (3, -1),
    (4, -1),
    (5, -1),
    (6, 0),
    (7, 0),
    (8, 0),
    (9, 1),
    (10, 1),
    (11, 1),
    (12, 2),
    (13, 2),
    (14, 2),
    (15, 3),
    (16, 3),
    (17, 3),
    (18, 4),
    (19, 4),
    (20, 4),
    (21, 5),
    (22, 5),
    (23, 5),
    (24, 6),
    (25, 6),
    (26, 6),
    (27, 7),
    (28, 7),
    (29, 7),
    (30, 8),
    (31, 8),
    (32, 8),
    (33, 9),
]


def test_characteristic_modifier_all_bands() -> None:
    for score, expected_mod in MODIFIER_TABLE:
        result = characteristic_modifier(score)
        assert (
            result == expected_mod
        ), f"characteristic_modifier({score}) expected {expected_mod}, got {result}"


def test_characteristic_modifier_above_33() -> None:
    assert characteristic_modifier(34) == 9
    assert characteristic_modifier(100) == 9


def test_characteristic_modifier_floor_is_minus_2() -> None:
    assert characteristic_modifier(0) == -2
    assert characteristic_modifier(2) == -2


def test_encode_upp_produces_6_char_string() -> None:
    scores = {
        "Strength": 7,
        "Dexterity": 10,
        "Endurance": 6,
        "Intelligence": 11,
        "Education": 8,
        "Social Standing": 5,
    }
    upp = encode_upp(scores)
    assert len(upp) == 6
    assert upp == "7A6B85"


def test_generation_failure_exit_code_is_1() -> None:
    failure = GenerationFailure(reason="test")
    assert failure.exit_code == 1


def test_generation_failure_stores_reason() -> None:
    failure = GenerationFailure(reason="Navy enlistment failed")
    assert failure.reason == "Navy enlistment failed"
