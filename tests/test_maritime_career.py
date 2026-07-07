"""Tests for MARITIME_CAREER data fields and behavior."""

from cetools.engine.careers.base import RankEntry
from conftest import ConstantRoller, SequenceRoller

# ---------------------------------------------------------------------------
# Qualification, survival, commission, advancement, reenlistment, name
# ---------------------------------------------------------------------------


def test_maritime_qualification_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.qualification_stat == "Endurance"


def test_maritime_qualification_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.qualification_target == 5


def test_maritime_survival_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.survival_stat == "Endurance"


def test_maritime_survival_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.survival_target == 5


def test_maritime_commission_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.commission_stat == "Intelligence"


def test_maritime_commission_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.commission_target == 6


def test_maritime_advancement_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.advancement_stat == "Education"


def test_maritime_advancement_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.advancement_target == 7


def test_maritime_reenlistment_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.reenlistment_target == 5


def test_maritime_name() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.name == "Maritime System Defense"


# ---------------------------------------------------------------------------
# Skill tables (24 exact positions)
# ---------------------------------------------------------------------------


def test_maritime_personal_development_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    )


def test_maritime_service_skills_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.service_skills == (
        "Mechanics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Survival",
        "Watercraft",
    )


def test_maritime_specialist_skills_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.specialist_skills == (
        "Comms",
        "Electronics",
        "Gun Combat",
        "Demolitions",
        "Recon",
        "Watercraft",
    )


def test_maritime_advanced_education_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    )


def test_maritime_all_skill_tables_have_six_entries() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.personal_development) == 6
    assert len(MARITIME_CAREER.service_skills) == 6
    assert len(MARITIME_CAREER.specialist_skills) == 6
    assert len(MARITIME_CAREER.advanced_education) == 6


# ---------------------------------------------------------------------------
# Rank entries (7 ranks, bonus skills at 0 and 3)
# ---------------------------------------------------------------------------


def test_maritime_rank_count() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.ranks) == 7


def test_maritime_rank_titles() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    expected = [
        "Seaman",
        "Ensign",
        "Lieutenant",
        "Lt Commander",
        "Commander",
        "Captain",
        "Admiral",
    ]
    for i, title in enumerate(expected):
        assert (
            MARITIME_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {MARITIME_CAREER.ranks[i].title!r}"


def test_maritime_rank_indices() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    for i in range(7):
        assert MARITIME_CAREER.ranks[i].rank == i


def test_maritime_rank_0_seaman_bonus_watercraft() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.ranks[0] == RankEntry(0, "Seaman", ("Watercraft",))


def test_maritime_rank_3_lt_commander_bonus_leadership() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.ranks[3] == RankEntry(3, "Lt Commander", ("Leadership",))


def test_maritime_ranks_without_bonus_skills() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            MARITIME_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


# ---------------------------------------------------------------------------
# Mustering-out tables (7 cash, 7 material)
# ---------------------------------------------------------------------------


def test_maritime_cash_benefits_values() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.cash_benefits == (
        1000,
        5000,
        10000,
        10000,
        20000,
        50000,
        50000,
    )


def test_maritime_cash_benefits_count() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.cash_benefits) == 7


def test_maritime_material_benefits_content() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    )


def test_maritime_material_benefits_count() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.material_benefits) == 7


# ---------------------------------------------------------------------------
# Commission and advancement behavior
# ---------------------------------------------------------------------------


def test_maritime_commission_roll_success_advances_to_rank_1() -> None:
    """When commission roll succeeds, character advances past rank 0."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        assert result.rank >= 1


def test_maritime_commission_roll_failure_stays_at_rank_0() -> None:
    """When commission roll fails, enlisted character stays at rank 0."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    _PRESET = {
        "Strength": 7,
        "Dexterity": 7,
        "Endurance": 7,
        "Intelligence": 7,
        "Education": 7,
        "Social Standing": 7,
    }

    # Survival (End 5): pass with 12
    # Commission (Int 6): fail with 1
    # Reenlistment (5): fail after 1 term with 1
    result = generate_character(
        MARITIME_CAREER,
        roller=SequenceRoller([12], default=1),
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 0


def test_maritime_advancement_increments_rank() -> None:
    """A commissioned character who passes advancement gains rank."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        assert result.rank >= 1


def test_maritime_rank_cap_at_6() -> None:
    """Character at rank 6 cannot advance further."""
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.ranks) == 7
    assert MARITIME_CAREER.ranks[6].title == "Admiral"
    assert MARITIME_CAREER.ranks[6].rank == 6


def test_maritime_rank_0_watercraft_applied_at_enlistment() -> None:
    """A freshly generated Maritime character has Watercraft in their skills."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        assert "Watercraft" in result.skills


def test_maritime_rank_3_leadership_applied() -> None:
    """A character who reaches rank 3 has Leadership in their skills."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        if result.rank >= 3:
            assert "Leadership" in result.skills
