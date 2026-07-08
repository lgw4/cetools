from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.rogue import ROGUE_CAREER


def test_rogue_scalar_fields() -> None:
    assert ROGUE_CAREER.name == "Rogue"
    assert ROGUE_CAREER.qualification_stat == "Dexterity"
    assert ROGUE_CAREER.qualification_target == 5
    assert ROGUE_CAREER.survival_stat == "Dexterity"
    assert ROGUE_CAREER.survival_target == 4
    assert ROGUE_CAREER.commission_stat == "Strength"
    assert ROGUE_CAREER.commission_target == 6
    assert ROGUE_CAREER.advancement_stat == "Intelligence"
    assert ROGUE_CAREER.advancement_target == 7
    assert ROGUE_CAREER.reenlistment_target == 4


def test_rogue_skill_tables() -> None:
    assert ROGUE_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Melee Combat",
        "Bribery",
        "Gambling",
    )
    assert ROGUE_CAREER.service_skills == (
        "Streetwise",
        "Mechanics",
        "Gun Combat",
        "Melee Combat",
        "Recon",
        "Vehicle",
    )
    assert ROGUE_CAREER.specialist_skills == (
        "Computer",
        "Electronics",
        "Bribery",
        "Broker",
        "Recon",
        "Vehicle",
    )
    assert ROGUE_CAREER.advanced_education == (
        "Computer",
        "Gravitics",
        "Jack o' Trades",
        "Medicine",
        "Advocate",
        "Tactics",
    )


def test_rogue_ranks() -> None:
    assert ROGUE_CAREER.ranks == (
        RankEntry(0, "Independent", ("Streetwise",)),
        RankEntry(1, "Associate", ()),
        RankEntry(2, "Soldier", ("Gun Combat",)),
        RankEntry(3, "Lieutenant", ()),
        RankEntry(4, "Underboss", ()),
        RankEntry(5, "Consigliere", ()),
        RankEntry(6, "Boss", ()),
    )


def test_rogue_benefits() -> None:
    assert ROGUE_CAREER.cash_benefits == (1000, 5000, 5000, 5000, 10000, 20000, 50000)
    assert ROGUE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    )
