from cetools.engine.careers.athlete import ATHLETE_CAREER
from cetools.engine.careers.base import RankEntry


def test_athlete_scalar_fields() -> None:
    assert ATHLETE_CAREER.name == "Athlete"
    assert ATHLETE_CAREER.qualification_stat == "Endurance"
    assert ATHLETE_CAREER.qualification_target == 8
    assert ATHLETE_CAREER.survival_stat == "Dexterity"
    assert ATHLETE_CAREER.survival_target == 5
    assert ATHLETE_CAREER.commission_stat is None
    assert ATHLETE_CAREER.commission_target is None
    assert ATHLETE_CAREER.advancement_stat is None
    assert ATHLETE_CAREER.advancement_target is None
    assert ATHLETE_CAREER.reenlistment_target == 6


def test_athlete_skill_tables() -> None:
    assert ATHLETE_CAREER.personal_development == (
        "+1 Dex",
        "+1 Int",
        "+1 Edu",
        "+1 Soc",
        "Carousing",
        "Melee Combat",
    )
    assert ATHLETE_CAREER.service_skills == (
        "Athletics",
        "Admin",
        "Carousing",
        "Computer",
        "Gambling",
        "Vehicle",
    )
    assert ATHLETE_CAREER.specialist_skills == (
        "Zero-G",
        "Athletics",
        "Athletics",
        "Computer",
        "Leadership",
        "Gambling",
    )
    assert ATHLETE_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Liaison",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_athlete_ranks() -> None:
    assert ATHLETE_CAREER.ranks == (RankEntry(0, "Athlete", ("Athletics",)),)


def test_athlete_benefits() -> None:
    assert ATHLETE_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert ATHLETE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "Explorers' Society",
        "High Passage",
    )
