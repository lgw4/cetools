from cetools.engine.careers.navy import NAVY_CAREER


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
