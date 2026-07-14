import pytest

from cetools.engine.aging import apply_aging
from cetools.engine.rolls import RollName
from conftest import scripted

_STATS = {
    "Strength": 12,
    "Dexterity": 12,
    "Endurance": 12,
    "Intelligence": 12,
    "Education": 12,
    "Social Standing": 12,
}


@pytest.mark.parametrize(
    ("roll", "terms", "strength", "dexterity", "endurance", "intelligence"),
    [
        (7, 4, 12, 12, 12, 12),  # 7-4 = 3   -> unhurt
        (5, 4, 12, 12, 12, 12),  # 5-4 = 1   -> unhurt, the boundary
        (4, 4, 11, 12, 12, 12),  # 4-4 = 0   -> Str-1
        (3, 4, 11, 11, 12, 12),  # 3-4 = -1  -> Str-1, Dex-1
        (2, 4, 11, 11, 11, 12),  # 2-4 = -2  -> Str/Dex/End -1
        (2, 5, 10, 11, 11, 12),  # 2-5 = -3  -> Str-2, Dex-1, End-1
        (2, 6, 10, 10, 11, 12),  # 2-6 = -4  -> Str-2, Dex-2, End-1
        (2, 7, 10, 10, 10, 12),  # 2-7 = -5  -> Str/Dex/End -2
        (2, 8, 10, 10, 10, 11),  # 2-8 = -6  -> and Intelligence-1
    ],
    ids=["3", "1", "0", "-1", "-2", "-3", "-4", "-5", "-6"],
)
def test_aging_ladder(
    roll: int,
    terms: int,
    strength: int,
    dexterity: int,
    endurance: int,
    intelligence: int,
) -> None:
    # The rung is (2D6 - terms_served). Anything of 1 or more leaves the character
    # unhurt. The last rung is only reachable in an 8th term: 2D6 bottoms out at 2
    # and the term cap is 7, so 2 - 7 = -5 is the worst an ordinary career sees.
    # tests/test_generator.py proves that end-to-end via a natural 12.
    aged = apply_aging(_STATS, terms, scripted(two_d6={RollName.AGING: roll}))
    assert aged["Strength"] == strength
    assert aged["Dexterity"] == dexterity
    assert aged["Endurance"] == endurance
    assert aged["Intelligence"] == intelligence


def test_aging_never_reduces_a_characteristic_below_zero() -> None:
    frail = dict(_STATS, Strength=1, Dexterity=1, Endurance=1)
    aged = apply_aging(frail, 8, scripted(two_d6={RollName.AGING: 2}))
    assert aged["Strength"] == 0
    assert aged["Dexterity"] == 0
    assert aged["Endurance"] == 0


def test_aging_leaves_non_physical_characteristics_alone_except_at_the_worst_rung() -> None:
    aged = apply_aging(_STATS, 7, scripted(two_d6={RollName.AGING: 2}))
    assert aged["Education"] == 12
    assert aged["Social Standing"] == 12
    assert aged["Intelligence"] == 12


def test_aging_does_not_mutate_its_argument() -> None:
    characteristics = dict(_STATS)
    apply_aging(characteristics, 8, scripted(two_d6={RollName.AGING: 2}))
    assert characteristics == _STATS
