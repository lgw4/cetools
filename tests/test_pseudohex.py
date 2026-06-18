import pytest

from cetools.engine.pseudohex import encode_upp, from_pseudohex, to_pseudohex

FULL_TABLE = [
    (0, "0"),
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (5, "5"),
    (6, "6"),
    (7, "7"),
    (8, "8"),
    (9, "9"),
    (10, "A"),
    (11, "B"),
    (12, "C"),
    (13, "D"),
    (14, "E"),
    (15, "F"),
    (16, "G"),
    (17, "H"),
    (18, "J"),  # I is skipped
    (19, "K"),
    (20, "L"),
    (21, "M"),
    (22, "N"),
    (23, "P"),  # O is skipped
    (24, "Q"),
    (25, "R"),
    (26, "S"),
    (27, "T"),
    (28, "U"),
    (29, "V"),
    (30, "W"),
    (31, "X"),
    (32, "Y"),
    (33, "Z"),
]


def test_to_pseudohex_all_34_values() -> None:
    for value, expected_char in FULL_TABLE:
        assert (
            to_pseudohex(value) == expected_char
        ), f"to_pseudohex({value}) expected {expected_char!r}"


def test_to_pseudohex_boundary_9_to_A() -> None:
    assert to_pseudohex(9) == "9"
    assert to_pseudohex(10) == "A"


def test_to_pseudohex_boundary_17_to_H_skips_I() -> None:
    assert to_pseudohex(17) == "H"
    assert to_pseudohex(18) == "J"


def test_to_pseudohex_boundary_22_to_N_skips_O() -> None:
    assert to_pseudohex(22) == "N"
    assert to_pseudohex(23) == "P"


def test_to_pseudohex_max_33_is_Z() -> None:
    assert to_pseudohex(33) == "Z"


def test_to_pseudohex_out_of_range_raises() -> None:
    with pytest.raises(ValueError):
        to_pseudohex(34)
    with pytest.raises(ValueError):
        to_pseudohex(-1)


def test_from_pseudohex_all_34_values() -> None:
    for value, char in FULL_TABLE:
        assert from_pseudohex(char) == value, f"from_pseudohex({char!r}) expected {value}"


def test_from_pseudohex_invalid_I_raises() -> None:
    with pytest.raises(ValueError):
        from_pseudohex("I")


def test_from_pseudohex_invalid_O_raises() -> None:
    with pytest.raises(ValueError):
        from_pseudohex("O")


def test_encode_upp_six_chars() -> None:
    scores = {
        "Strength": 6,
        "Dexterity": 8,
        "Endurance": 7,
        "Intelligence": 11,
        "Education": 9,
        "Social Standing": 12,
    }
    upp = encode_upp(scores)
    assert len(upp) == 6
    assert isinstance(upp, str)


def test_encode_upp_srd_example() -> None:
    # SRD example: 687B9C-4 → scores 6, 8, 7, 11, 9, 12
    scores = {
        "Strength": 6,
        "Dexterity": 8,
        "Endurance": 7,
        "Intelligence": 11,
        "Education": 9,
        "Social Standing": 12,
    }
    upp = encode_upp(scores)
    assert upp == "687B9C"


def test_encode_upp_order_is_srd_canonical() -> None:
    scores = {
        "Strength": 10,
        "Dexterity": 0,
        "Endurance": 1,
        "Intelligence": 2,
        "Education": 3,
        "Social Standing": 33,
    }
    upp = encode_upp(scores)
    assert upp[0] == "A"  # Strength 10
    assert upp[1] == "0"  # Dexterity 0
    assert upp[2] == "1"  # Endurance 1
    assert upp[3] == "2"  # Intelligence 2
    assert upp[4] == "3"  # Education 3
    assert upp[5] == "Z"  # Social Standing 33


def test_encode_upp_no_I_or_O() -> None:
    for score in range(34):
        scores = {
            "Strength": score,
            "Dexterity": score,
            "Endurance": score,
            "Intelligence": score,
            "Education": score,
            "Social Standing": score,
        }
        upp = encode_upp(scores)
        assert "I" not in upp, f"UPP contains 'I' for score {score}"
        assert "O" not in upp, f"UPP contains 'O' for score {score}"
