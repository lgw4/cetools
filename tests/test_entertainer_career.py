from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER


def test_entertainer_scalar_fields() -> None:
    assert ENTERTAINER_CAREER.name == "Entertainer"
    assert ENTERTAINER_CAREER.qualification_stat == "Social Standing"
    assert ENTERTAINER_CAREER.qualification_target == 8
    assert ENTERTAINER_CAREER.survival_stat == "Intelligence"
    assert ENTERTAINER_CAREER.survival_target == 4
    assert ENTERTAINER_CAREER.commission_stat is None
    assert ENTERTAINER_CAREER.commission_target is None
    assert ENTERTAINER_CAREER.advancement_stat is None
    assert ENTERTAINER_CAREER.advancement_target is None
    assert ENTERTAINER_CAREER.reenlistment_target == 6


def test_entertainer_skill_tables() -> None:
    assert ENTERTAINER_CAREER.personal_development == (
        "+1 Dex",
        "+1 Int",
        "+1 Edu",
        "+1 Soc",
        "Carousing",
        "Melee Combat",
    )
    assert ENTERTAINER_CAREER.service_skills == (
        "Athletics",
        "Admin",
        "Carousing",
        "Bribery",
        "Gambling",
        "Vehicle",
    )
    assert ENTERTAINER_CAREER.specialist_skills == (
        "Computer",
        "Carousing",
        "Bribery",
        "Liaison",
        "Gambling",
        "Recon",
    )
    assert ENTERTAINER_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Carousing",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_entertainer_ranks() -> None:
    assert ENTERTAINER_CAREER.ranks == (RankEntry(0, "Entertainer", ("Carousing",)),)


def test_entertainer_benefits() -> None:
    assert ENTERTAINER_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert ENTERTAINER_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
        "High Passage",
    )
