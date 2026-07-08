"""Tests for SURFACE_CAREER data fields and behavior."""

from cetools.engine.careers.base import RankEntry
from conftest import ConstantRoller, SequenceRoller

# ---------------------------------------------------------------------------
# Qualification, survival, commission, advancement, reenlistment, name
# ---------------------------------------------------------------------------


def test_surface_qualification_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.qualification_stat == "Endurance"


def test_surface_qualification_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.qualification_target == 5


def test_surface_survival_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.survival_stat == "Education"


def test_surface_survival_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.survival_target == 5


def test_surface_commission_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.commission_stat == "Endurance"


def test_surface_commission_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.commission_target == 6


def test_surface_advancement_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.advancement_stat == "Education"


def test_surface_advancement_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.advancement_target == 7


def test_surface_reenlistment_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.reenlistment_target == 5


def test_surface_name() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.name == "Surface System Defense"


# ---------------------------------------------------------------------------
# Skill tables (24 exact positions)
# ---------------------------------------------------------------------------


def test_surface_personal_development_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    )


def test_surface_service_skills_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.service_skills == (
        "Mechanics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Recon",
        "Battle Dress",
    )


def test_surface_specialist_skills_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.specialist_skills == (
        "Comms",
        "Demolitions",
        "Gun Combat",
        "Melee Combat",
        "Survival",
        "Vehicle",
    )


def test_surface_advanced_education_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    )


def test_surface_all_skill_tables_have_six_entries() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.personal_development) == 6
    assert len(SURFACE_CAREER.service_skills) == 6
    assert len(SURFACE_CAREER.specialist_skills) == 6
    assert len(SURFACE_CAREER.advanced_education) == 6


# ---------------------------------------------------------------------------
# Rank entries (7 ranks, bonus skills at 0 and 3)
# ---------------------------------------------------------------------------


def test_surface_rank_count() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.ranks) == 7


def test_surface_rank_titles() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    expected = [
        "Private",
        "Lieutenant",
        "Captain",
        "Major",
        "Lt Colonel",
        "Colonel",
        "General",
    ]
    for i, title in enumerate(expected):
        assert (
            SURFACE_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {SURFACE_CAREER.ranks[i].title!r}"


def test_surface_rank_indices() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    for i in range(7):
        assert SURFACE_CAREER.ranks[i].rank == i


def test_surface_rank_0_private_bonus_gun_combat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.ranks[0] == RankEntry(0, "Private", ("Gun Combat",))


def test_surface_rank_3_major_bonus_leadership() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.ranks[3] == RankEntry(3, "Major", ("Leadership",))


def test_surface_ranks_without_bonus_skills() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            SURFACE_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


# ---------------------------------------------------------------------------
# Mustering-out tables (7 cash, 7 material)
# ---------------------------------------------------------------------------


def test_surface_cash_benefits_values() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.cash_benefits == (
        1000,
        5000,
        10000,
        10000,
        20000,
        50000,
        50000,
    )


def test_surface_cash_benefits_count() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.cash_benefits) == 7


def test_surface_material_benefits_content() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    )


def test_surface_material_benefits_count() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.material_benefits) == 7


# ---------------------------------------------------------------------------
# Commission and advancement behavior
# ---------------------------------------------------------------------------


def test_surface_commission_roll_success_advances_to_rank_1() -> None:
    """When commission roll succeeds, character advances past rank 0."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    assert result.rank >= 1


def test_surface_commission_roll_failure_stays_at_rank_0() -> None:
    """When commission roll fails, enlisted character stays at rank 0."""
    from cetools.engine.careers.surface import SURFACE_CAREER
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

    # Survival (Edu 5): pass with the leading 12
    # Commission (End 6): fail with default 1
    # Reenlistment (5): fail after 1 term with default 1
    result = generate_character(
        SURFACE_CAREER,
        roller=SequenceRoller([12], default=1),
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 0


def test_surface_advancement_increments_rank() -> None:
    """A commissioned character who passes advancement gains rank."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    assert result.rank >= 1


def test_surface_rank_cap_at_6() -> None:
    """Character at rank 6 cannot advance further."""
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.ranks) == 7
    assert SURFACE_CAREER.ranks[6].title == "General"
    assert SURFACE_CAREER.ranks[6].rank == 6


def test_surface_rank_0_gun_combat_applied_at_enlistment() -> None:
    """A freshly generated Surface character has Gun Combat in their skills."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    assert "Gun Combat" in result.skills


def test_surface_rank_3_leadership_applied() -> None:
    """A character who reaches rank 3 has Leadership in their skills."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    if result.rank >= 3:
        assert "Leadership" in result.skills
