from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.pirate import PIRATE_CAREER


def test_pirate_scalar_fields() -> None:
    assert PIRATE_CAREER.name == "Pirate"
    assert PIRATE_CAREER.qualification_stat == "Dexterity"
    assert PIRATE_CAREER.qualification_target == 5
    assert PIRATE_CAREER.survival_stat == "Dexterity"
    assert PIRATE_CAREER.survival_target == 6
    assert PIRATE_CAREER.commission_stat == "Strength"
    assert PIRATE_CAREER.commission_target == 7
    assert PIRATE_CAREER.advancement_stat == "Intelligence"
    assert PIRATE_CAREER.advancement_target == 6
    assert PIRATE_CAREER.reenlistment_target == 5


def test_pirate_skill_tables() -> None:
    assert PIRATE_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Melee Combat",
        "Bribery",
        "Gambling",
    )
    assert PIRATE_CAREER.service_skills == (
        "Streetwise",
        "Electronics",
        "Gun Combat",
        "Melee Combat",
        "Recon",
        "Vehicle",
    )
    assert PIRATE_CAREER.specialist_skills == (
        "Zero-G",
        "Comms",
        "Engineering",
        "Gunnery",
        "Navigation",
        "Piloting",
    )
    assert PIRATE_CAREER.advanced_education == (
        "Computer",
        "Gravitics",
        "Jack o' Trades",
        "Medicine",
        "Advocate",
        "Tactics",
    )


def test_pirate_ranks() -> None:
    assert PIRATE_CAREER.ranks == (
        RankEntry(0, "Crewman", ("Gunnery",)),
        RankEntry(1, "Corporal", ()),
        RankEntry(2, "Lieutenant", ("Piloting",)),
        RankEntry(3, "Lt Commander", ()),
        RankEntry(4, "Commander", ()),
        RankEntry(5, "Captain", ()),
        RankEntry(6, "Commodore", ()),
    )


def test_pirate_benefits() -> None:
    assert PIRATE_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert PIRATE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "+1 Soc",
        "High Passage",
        "1D6 Ship Shares",
    )
