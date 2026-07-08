from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.mercenary import MERCENARY_CAREER


def test_mercenary_scalar_fields() -> None:
    assert MERCENARY_CAREER.name == "Mercenary"
    assert MERCENARY_CAREER.qualification_stat == "Intelligence"
    assert MERCENARY_CAREER.qualification_target == 4
    assert MERCENARY_CAREER.survival_stat == "Endurance"
    assert MERCENARY_CAREER.survival_target == 6
    assert MERCENARY_CAREER.commission_stat == "Intelligence"
    assert MERCENARY_CAREER.commission_target == 7
    assert MERCENARY_CAREER.advancement_stat == "Intelligence"
    assert MERCENARY_CAREER.advancement_target == 6
    assert MERCENARY_CAREER.reenlistment_target == 5


def test_mercenary_skill_tables() -> None:
    assert MERCENARY_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Zero-G",
        "Melee Combat",
        "Gambling",
    )
    assert MERCENARY_CAREER.service_skills == (
        "Comms",
        "Mechanics",
        "Gun Combat",
        "Melee Combat",
        "Gambling",
        "Battle Dress",
    )
    assert MERCENARY_CAREER.specialist_skills == (
        "Gravitics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Recon",
        "Vehicle",
    )
    assert MERCENARY_CAREER.advanced_education == (
        "Advocate",
        "Engineering",
        "Medicine",
        "Navigation",
        "Sciences",
        "Tactics",
    )


def test_mercenary_ranks() -> None:
    assert MERCENARY_CAREER.ranks == (
        RankEntry(0, "Private", ("Gun Combat",)),
        RankEntry(1, "Lieutenant", ()),
        RankEntry(2, "Captain", ()),
        RankEntry(3, "Major", ("Tactics",)),
        RankEntry(4, "Lt Colonel", ()),
        RankEntry(5, "Colonel", ()),
        RankEntry(6, "Brigadier", ()),
    )


def test_mercenary_benefits() -> None:
    assert MERCENARY_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert MERCENARY_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "+1 Soc",
        "High Passage",
        "1D6 Ship Shares",
    )
