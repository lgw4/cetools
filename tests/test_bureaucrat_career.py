from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER


def test_bureaucrat_scalar_fields() -> None:
    assert BUREAUCRAT_CAREER.name == "Bureaucrat"
    assert BUREAUCRAT_CAREER.qualification_stat == "Social Standing"
    assert BUREAUCRAT_CAREER.qualification_target == 6
    assert BUREAUCRAT_CAREER.survival_stat == "Education"
    assert BUREAUCRAT_CAREER.survival_target == 4
    assert BUREAUCRAT_CAREER.commission_stat == "Social Standing"
    assert BUREAUCRAT_CAREER.commission_target == 5
    assert BUREAUCRAT_CAREER.advancement_stat == "Intelligence"
    assert BUREAUCRAT_CAREER.advancement_target == 8
    assert BUREAUCRAT_CAREER.reenlistment_target == 5


def test_bureaucrat_skill_tables() -> None:
    assert BUREAUCRAT_CAREER.personal_development == (
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Athletics",
        "Carousing",
    )
    assert BUREAUCRAT_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Carousing",
        "Bribery",
        "Leadership",
        "Vehicle",
    )
    assert BUREAUCRAT_CAREER.specialist_skills == (
        "Admin",
        "Computer",
        "Perception",
        "Leadership",
        "Steward",
        "Vehicle",
    )
    assert BUREAUCRAT_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Liaison",
        "Linguistics",
        "Medicine",
        "Admin",
    )


def test_bureaucrat_ranks() -> None:
    assert BUREAUCRAT_CAREER.ranks == (
        RankEntry(0, "Assistant", ("Admin",)),
        RankEntry(1, "Clerk", ()),
        RankEntry(2, "Supervisor", ()),
        RankEntry(3, "Manager", ()),
        RankEntry(4, "Chief", ("Advocate",)),
        RankEntry(5, "Director", ()),
        RankEntry(6, "Minister", ()),
    )


def test_bureaucrat_benefits() -> None:
    assert BUREAUCRAT_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert BUREAUCRAT_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
    )
