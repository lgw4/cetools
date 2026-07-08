from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.hunter import HUNTER_CAREER


def test_hunter_scalar_fields() -> None:
    assert HUNTER_CAREER.name == "Hunter"
    assert HUNTER_CAREER.qualification_stat == "Endurance"
    assert HUNTER_CAREER.qualification_target == 5
    assert HUNTER_CAREER.survival_stat == "Strength"
    assert HUNTER_CAREER.survival_target == 8
    assert HUNTER_CAREER.commission_stat is None
    assert HUNTER_CAREER.commission_target is None
    assert HUNTER_CAREER.advancement_stat is None
    assert HUNTER_CAREER.advancement_target is None
    assert HUNTER_CAREER.reenlistment_target == 6


def test_hunter_skill_tables() -> None:
    assert HUNTER_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "Athletics",
        "Gun Combat",
    )
    assert HUNTER_CAREER.service_skills == (
        "Mechanics",
        "Gun Combat",
        "Melee Combat",
        "Recon",
        "Survival",
        "Vehicle",
    )
    assert HUNTER_CAREER.specialist_skills == (
        "Admin",
        "Comms",
        "Electronics",
        "Recon",
        "Animals",
        "Vehicle",
    )
    assert HUNTER_CAREER.advanced_education == (
        "Advocate",
        "Linguistics",
        "Medicine",
        "Liaison",
        "Animals",
        "Animals",
    )


def test_hunter_ranks() -> None:
    assert HUNTER_CAREER.ranks == (RankEntry(0, "Hunter", ("Survival",)),)


def test_hunter_benefits() -> None:
    assert HUNTER_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert HUNTER_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "1D6 Ship Shares",
        "High Passage",
    )
