from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.scientist import SCIENTIST_CAREER


def test_scientist_scalar_fields() -> None:
    assert SCIENTIST_CAREER.name == "Scientist"
    assert SCIENTIST_CAREER.qualification_stat == "Education"
    assert SCIENTIST_CAREER.qualification_target == 6
    assert SCIENTIST_CAREER.survival_stat == "Education"
    assert SCIENTIST_CAREER.survival_target == 5
    assert SCIENTIST_CAREER.commission_stat == "Intelligence"
    assert SCIENTIST_CAREER.commission_target == 7
    assert SCIENTIST_CAREER.advancement_stat == "Intelligence"
    assert SCIENTIST_CAREER.advancement_target == 6
    assert SCIENTIST_CAREER.reenlistment_target == 5


def test_scientist_skill_tables() -> None:
    assert SCIENTIST_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Gun Combat",
    )
    assert SCIENTIST_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Electronics",
        "Medicine",
        "Bribery",
        "Sciences",
    )
    assert SCIENTIST_CAREER.specialist_skills == (
        "Navigation",
        "Admin",
        "Sciences",
        "Sciences",
        "Animals",
        "Vehicle",
    )
    assert SCIENTIST_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_scientist_ranks() -> None:
    assert SCIENTIST_CAREER.ranks == (
        RankEntry(0, "Instructor", ("Sciences",)),
        RankEntry(1, "Adjunct Professor", ()),
        RankEntry(2, "Research Professor", ()),
        RankEntry(3, "Assistant Professor", ("Computer",)),
        RankEntry(4, "Associate Professor", ()),
        RankEntry(5, "Professor", ()),
        RankEntry(6, "Distinguished Professor", ()),
    )


def test_scientist_benefits() -> None:
    assert SCIENTIST_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert SCIENTIST_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Research Vessel",
    )
