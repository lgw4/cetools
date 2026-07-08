from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.base import RankEntry


def test_barbarian_scalar_fields() -> None:
    assert BARBARIAN_CAREER.name == "Barbarian"
    assert BARBARIAN_CAREER.qualification_stat == "Endurance"
    assert BARBARIAN_CAREER.qualification_target == 5
    assert BARBARIAN_CAREER.survival_stat == "Strength"
    assert BARBARIAN_CAREER.survival_target == 6
    assert BARBARIAN_CAREER.commission_stat is None
    assert BARBARIAN_CAREER.commission_target is None
    assert BARBARIAN_CAREER.advancement_stat is None
    assert BARBARIAN_CAREER.advancement_target is None
    assert BARBARIAN_CAREER.reenlistment_target == 5


def test_barbarian_skill_tables() -> None:
    assert BARBARIAN_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "Athletics",
        "Gun Combat",
    )
    assert BARBARIAN_CAREER.service_skills == (
        "Gun Combat",
        "Melee Combat",
        "Recon",
        "Survival",
        "Animals",
        "Gun Combat",
    )
    assert BARBARIAN_CAREER.specialist_skills == (
        "Gun Combat",
        "Jack o' Trades",
        "Melee Combat",
        "Recon",
        "Animals",
        "Tactics",
    )
    assert BARBARIAN_CAREER.advanced_education == (
        "Advocate",
        "Linguistics",
        "Medicine",
        "Leadership",
        "Broker",
        "Tactics",
    )


def test_barbarian_ranks() -> None:
    assert BARBARIAN_CAREER.ranks == (RankEntry(0, "Barbarian", ("Melee Combat",)),)


def test_barbarian_benefits() -> None:
    assert BARBARIAN_CAREER.cash_benefits == (0, 1000, 2000, 5000, 5000, 10000, 10000)
    assert BARBARIAN_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Weapon",
        "+1 End",
        "Mid Passage",
    )
