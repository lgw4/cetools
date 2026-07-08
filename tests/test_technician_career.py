from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.technician import TECHNICIAN_CAREER


def test_technician_scalar_fields() -> None:
    assert TECHNICIAN_CAREER.name == "Technician"
    assert TECHNICIAN_CAREER.qualification_stat == "Education"
    assert TECHNICIAN_CAREER.qualification_target == 6
    assert TECHNICIAN_CAREER.survival_stat == "Dexterity"
    assert TECHNICIAN_CAREER.survival_target == 4
    assert TECHNICIAN_CAREER.commission_stat == "Education"
    assert TECHNICIAN_CAREER.commission_target == 5
    assert TECHNICIAN_CAREER.advancement_stat == "Intelligence"
    assert TECHNICIAN_CAREER.advancement_target == 8
    assert TECHNICIAN_CAREER.reenlistment_target == 5


def test_technician_skill_tables() -> None:
    assert TECHNICIAN_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Gun Combat",
    )
    assert TECHNICIAN_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Mechanics",
        "Medicine",
        "Electronics",
        "Sciences",
    )
    assert TECHNICIAN_CAREER.specialist_skills == (
        "Computer",
        "Electronics",
        "Gravitics",
        "Linguistics",
        "Engineering",
        "Animals",
    )
    assert TECHNICIAN_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_technician_ranks() -> None:
    assert TECHNICIAN_CAREER.ranks == (
        RankEntry(0, "Technician", ("Computer",)),
        RankEntry(1, "Team Lead", ()),
        RankEntry(2, "Supervisor", ()),
        RankEntry(3, "Manager", ()),
        RankEntry(4, "Director", ("Admin",)),
        RankEntry(5, "Vice-President", ()),
        RankEntry(6, "Executive Officer", ()),
    )


def test_technician_benefits() -> None:
    assert TECHNICIAN_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert TECHNICIAN_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
    )
