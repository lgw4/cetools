import pytest

from cetools.dice import Roller, parse_notation, throw, throw_dice
from cetools.errors import DiceError

# --- parse_notation: accepted forms ---


@pytest.mark.parametrize(
    "notation, expected",
    [
        ("2d6", (2, 6, 0)),
        ("d6", (1, 6, 0)),
        ("2D6+1", (2, 6, 1)),
        ("3d6 - 2", (3, 6, -2)),
        ("1d100", (1, 100, 0)),
        ("1d66", (1, 66, 0)),
    ],
)
def test_parse_notation_accepts(notation, expected):
    assert parse_notation(notation) == expected


# --- parse_notation: rejected forms ---


@pytest.mark.parametrize("notation", ["7dQ", "0d6", "2d0", ""])
def test_parse_notation_rejects(notation):
    with pytest.raises(DiceError):
        parse_notation(notation)


# --- Roller.die / Roller.dice ---


def test_die_sides_one_returns_face_one_via_getrandbits_zero():
    roller = Roller(0)
    assert roller.die(1) == 1


def test_dice_returns_tuple_of_requested_length():
    roller = Roller("session-alpha")
    faces = roller.dice(4, 6)
    assert isinstance(faces, tuple)
    assert len(faces) == 4
    assert all(1 <= face <= 6 for face in faces)


def test_die_raises_dice_error_for_sides_below_one():
    roller = Roller(0)
    with pytest.raises(DiceError):
        roller.die(0)


def test_dice_raises_dice_error_for_count_below_one():
    roller = Roller(0)
    with pytest.raises(DiceError):
        roller.dice(0, 6)


# --- throw / throw_dice: literal expected values ---


def test_throw_2d6_plus1_session_alpha_matches_published_table():
    result = throw(Roller("session-alpha"), "2d6+1")
    assert result.faces == (1, 5)
    assert result.modifier == 1
    assert result.total == 7
    assert result.notation == "2d6+1"
    assert result.seed == 14333185781139156525


def test_throw_dice_matches_throw():
    a = throw(Roller("session-alpha"), "2d6+1")
    b = throw_dice(Roller("session-alpha"), 2, 6, 1)
    assert a.faces == b.faces
    assert a.total == b.total


# --- FR-012: exhaustive d6 coverage over a large seeded sample ---


def test_seeded_sample_of_d6_faces_covers_all_six_values():
    roller = Roller("session-alpha")
    faces = roller.dice(1000, 6)
    assert set(faces) == {1, 2, 3, 4, 5, 6}


# --- FR-002: a seed is used exactly as given, sign included ---


def test_roller_reports_a_negative_seed_unchanged():
    assert Roller(-5).seed == -5
    assert Roller("-5").seed == -5


def test_negative_and_positive_seeds_of_the_same_magnitude_throw_differently():
    # FR-002 forbids reducing a seed into a narrower range, and `random.Random`
    # seeds an exact integer from its absolute value, so the sign has to survive
    # the hand-off or half the seed space is unreachable.
    assert throw(Roller(-5), "2d6").faces != throw(Roller(5), "2d6").faces


def test_negative_and_positive_seeds_above_2_64_throw_differently():
    huge = 2**200 + 7
    assert throw(Roller(-huge), "2d6").faces != throw(Roller(huge), "2d6").faces


def test_seed_above_2_64_round_trips_through_roller():
    huge = 2**64 + 12345
    first = throw(Roller(huge), "2d6")
    second = throw(Roller(str(huge)), "2d6")
    assert first.seed == huge
    assert first == second


def test_negative_seed_round_trips_through_its_reported_value():
    first = throw(Roller(-5), "2d6")
    second = throw(Roller(str(first.seed)), "2d6")
    assert first == second


# --- FR-008: roller independence ---


def test_two_rollers_drawn_alternately_do_not_consume_each_others_stream():
    solo_a = Roller("session-alpha").dice(20, 6)
    solo_b = Roller(1).dice(20, 6)

    roller_a = Roller("session-alpha")
    roller_b = Roller(1)
    interleaved_a = []
    interleaved_b = []
    for _ in range(20):
        interleaved_a.append(roller_a.die(6))
        interleaved_b.append(roller_b.die(6))

    assert tuple(interleaved_a) == solo_a
    assert tuple(interleaved_b) == solo_b
