from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.physician import PHYSICIAN_CAREER


def test_physician_scalar_fields() -> None:
    assert PHYSICIAN_CAREER.name == "Physician"
    assert PHYSICIAN_CAREER.qualification_stat == "Education"
    assert PHYSICIAN_CAREER.qualification_target == 6
    assert PHYSICIAN_CAREER.survival_stat == "Intelligence"
    assert PHYSICIAN_CAREER.survival_target == 4
    assert PHYSICIAN_CAREER.commission_stat == "Intelligence"
    assert PHYSICIAN_CAREER.commission_target == 5
    assert PHYSICIAN_CAREER.advancement_stat == "Education"
    assert PHYSICIAN_CAREER.advancement_target == 8
    assert PHYSICIAN_CAREER.reenlistment_target == 5


def test_physician_skill_tables() -> None:
    assert PHYSICIAN_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Gun Combat",
    )
    assert PHYSICIAN_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Mechanics",
        "Medicine",
        "Leadership",
        "Sciences",
    )
    assert PHYSICIAN_CAREER.specialist_skills == (
        "Computer",
        "Carousing",
        "Electronics",
        "Medicine",
        "Medicine",
        "Sciences",
    )
    assert PHYSICIAN_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_physician_ranks() -> None:
    assert PHYSICIAN_CAREER.ranks == (
        RankEntry(0, "Intern", ("Medicine",)),
        RankEntry(1, "Resident", ()),
        RankEntry(2, "Senior Resident", ()),
        RankEntry(3, "Chief Resident", ()),
        RankEntry(4, "Attending Physician", ("Admin",)),
        RankEntry(5, "Service Chief", ()),
        RankEntry(6, "Hospital Administrator", ()),
    )


def test_physician_benefits() -> None:
    assert PHYSICIAN_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert PHYSICIAN_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "High Passage",
        "Explorers' Society",
        "High Passage",
        "+1 Soc",
    )
