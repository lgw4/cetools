import dataclasses
import os

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate_character
from cetools.engine.models import Character, GenerationFailure


class _ConstantRoller:
    def __init__(self, value: int) -> None:
        self._value = value

    def roll(self, sides: int, count: int = 1) -> int:
        return self._value


class _SmartRoller:
    def __init__(self, two_dice_value: int, one_die_value: int) -> None:
        self._two = two_dice_value
        self._one = one_die_value

    def roll(self, sides: int, count: int = 1) -> int:
        return self._two if count >= 2 else self._one


def test_extensibility_stub_career_returns_character_or_failure() -> None:
    """A non-Navy Career passes through generate_character unchanged."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = _SmartRoller(two_dice_value=12, one_die_value=1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, (Character, GenerationFailure))


def test_extensibility_failure_path_with_stub_career() -> None:
    """A stub career with always-low rolls triggers enlistment failure."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = _ConstantRoller(1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, GenerationFailure)


def test_extensibility_result_uses_stub_career_name() -> None:
    """Character or failure reason reflects the stub career name, not 'Navy'."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = _ConstantRoller(1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, GenerationFailure)
    assert "Scout" in result.reason
    assert "Navy" not in result.reason


def test_extensibility_success_character_career_name() -> None:
    """Successful generation reflects the stub career name."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = _SmartRoller(two_dice_value=12, one_die_value=1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, Character)
    assert result.career == "Scout"


def test_generator_has_no_navy_literal() -> None:
    """No 'Navy' string literal in the engine generator source."""
    generator_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "cetools",
        "engine",
        "generator.py",
    )
    with open(os.path.normpath(generator_path)) as f:
        source = f.read()
    assert '"Navy"' not in source, 'Hardcoded "Navy" found in generator.py'
    assert "'Navy'" not in source, "Hardcoded 'Navy' found in generator.py"


def test_navy_qualification_stat_and_target() -> None:
    assert NAVY_CAREER.qualification_stat == "Intelligence"
    assert NAVY_CAREER.qualification_target == 6


def test_navy_survival_stat_and_target() -> None:
    assert NAVY_CAREER.survival_stat == "Intelligence"
    assert NAVY_CAREER.survival_target == 5


def test_navy_commission_stat_and_target() -> None:
    assert NAVY_CAREER.commission_stat == "Social Standing"
    assert NAVY_CAREER.commission_target == 7


def test_navy_advancement_stat_and_target() -> None:
    assert NAVY_CAREER.advancement_stat == "Education"
    assert NAVY_CAREER.advancement_target == 6


def test_navy_skill_tables_have_six_entries() -> None:
    assert len(NAVY_CAREER.service_skills) == 6
    assert len(NAVY_CAREER.personal_development) == 6
    assert len(NAVY_CAREER.specialist_skills) == 6
    assert len(NAVY_CAREER.advanced_education) == 6


def test_navy_benefit_tables_have_seven_entries() -> None:
    assert len(NAVY_CAREER.cash_benefits) == 7
    assert len(NAVY_CAREER.material_benefits) == 7


def test_navy_service_skills_content() -> None:
    assert NAVY_CAREER.service_skills == (
        "Comms",
        "Engineering",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Vehicle",
    )


def test_navy_rank_titles_match_srd() -> None:
    expected = [
        "Starman",
        "Midshipman",
        "Lieutenant",
        "Lt Commander",
        "Commander",
        "Captain",
        "Commodore",
    ]
    assert len(NAVY_CAREER.ranks) == 7
    for i, title in enumerate(expected):
        assert (
            NAVY_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {NAVY_CAREER.ranks[i].title!r}"


def test_navy_rank_0_grants_zero_g() -> None:
    assert "Zero-G" in NAVY_CAREER.ranks[0].bonus_skills


def test_navy_rank_3_grants_tactics() -> None:
    assert "Tactics" in NAVY_CAREER.ranks[3].bonus_skills


def test_navy_ranks_without_bonus_skills() -> None:
    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            NAVY_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


def test_navy_cash_benefits_values() -> None:
    assert NAVY_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)


def test_navy_material_benefits_content() -> None:
    assert NAVY_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Explorer's Society",
    )


def test_navy_reenlistment_target() -> None:
    assert NAVY_CAREER.reenlistment_target == 5


def test_navy_name() -> None:
    assert NAVY_CAREER.name == "Navy"
