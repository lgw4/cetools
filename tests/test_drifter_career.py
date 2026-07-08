from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.drifter import DRIFTER_CAREER


def test_drifter_scalar_fields() -> None:
    assert DRIFTER_CAREER.name == "Drifter"
    assert DRIFTER_CAREER.qualification_stat is None
    assert DRIFTER_CAREER.qualification_target is None
    assert DRIFTER_CAREER.survival_stat == "Endurance"
    assert DRIFTER_CAREER.survival_target == 5
    assert DRIFTER_CAREER.commission_stat is None
    assert DRIFTER_CAREER.commission_target is None
    assert DRIFTER_CAREER.advancement_stat is None
    assert DRIFTER_CAREER.advancement_target is None
    assert DRIFTER_CAREER.reenlistment_target == 5


def test_drifter_skill_tables() -> None:
    assert DRIFTER_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Melee Combat",
        "Bribery",
        "Gambling",
    )
    assert DRIFTER_CAREER.service_skills == (
        "Streetwise",
        "Mechanics",
        "Gun Combat",
        "Melee Combat",
        "Recon",
        "Vehicle",
    )
    assert DRIFTER_CAREER.specialist_skills == (
        "Electronics",
        "Melee Combat",
        "Bribery",
        "Streetwise",
        "Gambling",
        "Recon",
    )
    assert DRIFTER_CAREER.advanced_education == (
        "Computer",
        "Engineering",
        "Jack o' Trades",
        "Medicine",
        "Liaison",
        "Tactics",
    )


def test_drifter_ranks() -> None:
    assert DRIFTER_CAREER.ranks == (RankEntry(0, "Drifter", ()),)


def test_drifter_benefits() -> None:
    assert DRIFTER_CAREER.cash_benefits == (0, 1000, 2000, 5000, 5000, 10000, 10000)
    assert DRIFTER_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Weapon",
        "Mid Passage",
        "Mid Passage",
    )
