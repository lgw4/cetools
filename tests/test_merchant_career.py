from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.merchant import MERCHANT_CAREER


def test_merchant_scalar_fields() -> None:
    assert MERCHANT_CAREER.name == "Merchant"
    assert MERCHANT_CAREER.qualification_stat == "Intelligence"
    assert MERCHANT_CAREER.qualification_target == 4
    assert MERCHANT_CAREER.survival_stat == "Intelligence"
    assert MERCHANT_CAREER.survival_target == 5
    assert MERCHANT_CAREER.commission_stat == "Intelligence"
    assert MERCHANT_CAREER.commission_target == 5
    assert MERCHANT_CAREER.advancement_stat == "Education"
    assert MERCHANT_CAREER.advancement_target == 8
    assert MERCHANT_CAREER.reenlistment_target == 4


def test_merchant_skill_tables() -> None:
    assert MERCHANT_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Melee Combat",
        "Steward",
        "Gambling",
    )
    assert MERCHANT_CAREER.service_skills == (
        "Comms",
        "Engineering",
        "Gun Combat",
        "Melee Combat",
        "Broker",
        "Vehicle",
    )
    assert MERCHANT_CAREER.specialist_skills == (
        "Carousing",
        "Gunnery",
        "Jack o' Trades",
        "Medicine",
        "Navigation",
        "Piloting",
    )
    assert MERCHANT_CAREER.advanced_education == (
        "Advocate",
        "Engineering",
        "Medicine",
        "Navigation",
        "Sciences",
        "Tactics",
    )


def test_merchant_ranks() -> None:
    assert MERCHANT_CAREER.ranks == (
        RankEntry(0, "Crewman", ("Steward",)),
        RankEntry(1, "Deck Cadet", ()),
        RankEntry(2, "Fourth Officer", ()),
        RankEntry(3, "Third Officer", ("Piloting",)),
        RankEntry(4, "Second Officer", ()),
        RankEntry(5, "First Officer", ()),
        RankEntry(6, "Captain", ()),
    )


def test_merchant_benefits() -> None:
    assert MERCHANT_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert MERCHANT_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "High Passage",
        "1D6 Ship Shares",
        "High Passage",
        "Explorers' Society",
    )
