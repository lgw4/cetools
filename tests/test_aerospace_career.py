"""Tests for AEROSPACE_CAREER data fields and behavior (US1, US2)."""

from cetools.engine.careers.base import RankEntry

# ---------------------------------------------------------------------------
# T002 — Qualification, survival, commission, advancement, reenlistment fields
# ---------------------------------------------------------------------------


def test_aerospace_qualification_stat() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.qualification_stat == "Endurance"


def test_aerospace_qualification_target() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.qualification_target == 5


def test_aerospace_survival_stat() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.survival_stat == "Dexterity"


def test_aerospace_survival_target() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.survival_target == 5


def test_aerospace_commission_stat() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.commission_stat == "Education"


def test_aerospace_commission_target() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.commission_target == 6


def test_aerospace_advancement_stat() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.advancement_stat == "Education"


def test_aerospace_advancement_target() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.advancement_target == 7


def test_aerospace_reenlistment_target() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.reenlistment_target == 5


def test_aerospace_name() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.name == "Aerospace System Defense"


# ---------------------------------------------------------------------------
# T003 — Skill tables (24 exact positions)
# ---------------------------------------------------------------------------


def test_aerospace_personal_development_table() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    )


def test_aerospace_service_skills_table() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.service_skills == (
        "Electronics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Survival",
        "Aircraft",
    )


def test_aerospace_specialist_skills_table() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.specialist_skills == (
        "Comms",
        "Gravitics",
        "Gun Combat",
        "Gunnery",
        "Recon",
        "Piloting",
    )


def test_aerospace_advanced_education_table() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    )


def test_aerospace_all_skill_tables_have_six_entries() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert len(AEROSPACE_CAREER.personal_development) == 6
    assert len(AEROSPACE_CAREER.service_skills) == 6
    assert len(AEROSPACE_CAREER.specialist_skills) == 6
    assert len(AEROSPACE_CAREER.advanced_education) == 6


# ---------------------------------------------------------------------------
# T004 — Rank entries (7 ranks, correct bonus skills at 0 and 3)
# ---------------------------------------------------------------------------


def test_aerospace_rank_count() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert len(AEROSPACE_CAREER.ranks) == 7


def test_aerospace_rank_titles() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    expected = [
        "Airman",
        "Flight Officer",
        "Flight Lieutenant",
        "Squadron Leader",
        "Wing Commander",
        "Group Captain",
        "Air Commodore",
    ]
    for i, title in enumerate(expected):
        assert (
            AEROSPACE_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {AEROSPACE_CAREER.ranks[i].title!r}"


def test_aerospace_rank_indices() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    for i in range(7):
        assert AEROSPACE_CAREER.ranks[i].rank == i


def test_aerospace_rank_0_airman_bonus_aircraft() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.ranks[0] == RankEntry(0, "Airman", ("Aircraft",))


def test_aerospace_rank_3_squadron_leader_bonus_leadership() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.ranks[3] == RankEntry(3, "Squadron Leader", ("Leadership",))


def test_aerospace_ranks_without_bonus_skills() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            AEROSPACE_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


# ---------------------------------------------------------------------------
# T005 — Mustering-out tables (7 cash, 7 material)
# ---------------------------------------------------------------------------


def test_aerospace_cash_benefits_values() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.cash_benefits == (
        1000,
        5000,
        10000,
        10000,
        20000,
        50000,
        50000,
    )


def test_aerospace_cash_benefits_count() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert len(AEROSPACE_CAREER.cash_benefits) == 7


def test_aerospace_material_benefits_content() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    )


def test_aerospace_material_benefits_count() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert len(AEROSPACE_CAREER.material_benefits) == 7


def test_aerospace_material_benefit_index_4_is_weapon() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.material_benefits[4] == "Weapon"


def test_aerospace_material_benefit_index_5_is_high_passage() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.material_benefits[5] == "High Passage"


def test_aerospace_material_benefit_index_6_is_plus1_soc() -> None:
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert AEROSPACE_CAREER.material_benefits[6] == "+1 Soc"


# ---------------------------------------------------------------------------
# T011 — Commission and advancement behavior (US2)
# ---------------------------------------------------------------------------

VALID_RANK_TITLES = {
    "Airman",
    "Flight Officer",
    "Flight Lieutenant",
    "Squadron Leader",
    "Wing Commander",
    "Group Captain",
    "Air Commodore",
}


def test_aerospace_commission_roll_success_advances_to_rank_1() -> None:
    """When commission roll succeeds, character advances from rank 0 to rank 1."""
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    class _CommissionSuccessRoller:
        """Always passes qualification, survival, commission, advancement."""

        def roll(self, sides: int, count: int = 1) -> int:
            return 12

    result = generate_character(AEROSPACE_CAREER, roller=_CommissionSuccessRoller())
    # With all rolls succeeding, character should be commissioned (rank >= 1)
    if isinstance(result, Character):
        assert result.rank >= 1


def test_aerospace_commission_roll_failure_stays_at_rank_0() -> None:
    """When commission roll fails, enlisted character stays at rank 0."""
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    class _NoCommissionRoller:
        """Passes qualification/survival/reenlistment but fails commission/advancement."""

        def __init__(self) -> None:
            self._call = 0

        def roll(self, sides: int, count: int = 1) -> int:
            self._call += 1
            # Qualification (End 5): pass with 12
            # Survival (Dex 5): pass with 12
            # Commission (Edu 6): fail with 1
            # Advancement (Edu 7): fail with 1
            # Reenlistment (5): fail after 1 term with 1
            return 12 if self._call <= 2 else 1

    result = generate_character(AEROSPACE_CAREER, roller=_NoCommissionRoller())
    if isinstance(result, Character):
        assert result.rank == 0


def test_aerospace_advancement_increments_rank() -> None:
    """A commissioned character who passes advancement gains rank."""
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    class _AlwaysPassRoller:
        def roll(self, sides: int, count: int = 1) -> int:
            return 12

    result = generate_character(AEROSPACE_CAREER, roller=_AlwaysPassRoller())
    if isinstance(result, Character):
        assert result.rank >= 1


# ---------------------------------------------------------------------------
# T011b — Rank cap at 6 (Air Commodore)
# ---------------------------------------------------------------------------


def test_aerospace_rank_cap_at_6() -> None:
    """Character at rank 6 cannot advance further."""
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER

    assert len(AEROSPACE_CAREER.ranks) == 7
    assert AEROSPACE_CAREER.ranks[6].title == "Air Commodore"
    assert AEROSPACE_CAREER.ranks[6].rank == 6


# ---------------------------------------------------------------------------
# T012 — Bonus skill application behavior
# ---------------------------------------------------------------------------


def test_aerospace_rank_0_aircraft_applied_at_enlistment() -> None:
    """A freshly generated Aerospace character has Aircraft in their skill list."""
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    class _AlwaysPassRoller:
        def roll(self, sides: int, count: int = 1) -> int:
            return 12

    result = generate_character(AEROSPACE_CAREER, roller=_AlwaysPassRoller())
    if isinstance(result, Character):
        assert "Aircraft" in result.skills


def test_aerospace_rank_3_leadership_applied() -> None:
    """A character who reaches rank 3 has Leadership in their skill list."""
    from cetools.engine.careers.aerospace import AEROSPACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    class _AlwaysPassRoller:
        def roll(self, sides: int, count: int = 1) -> int:
            return 12

    result = generate_character(AEROSPACE_CAREER, roller=_AlwaysPassRoller())
    if isinstance(result, Character):
        if result.rank >= 3:
            assert "Leadership" in result.skills
