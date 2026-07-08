from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.noble import NOBLE_CAREER


def test_noble_scalar_fields() -> None:
    assert NOBLE_CAREER.name == "Noble"
    assert NOBLE_CAREER.qualification_stat == "Social Standing"
    assert NOBLE_CAREER.qualification_target == 8
    assert NOBLE_CAREER.survival_stat == "Social Standing"
    assert NOBLE_CAREER.survival_target == 4
    assert NOBLE_CAREER.commission_stat == "Education"
    assert NOBLE_CAREER.commission_target == 5
    assert NOBLE_CAREER.advancement_stat == "Intelligence"
    assert NOBLE_CAREER.advancement_target == 8
    assert NOBLE_CAREER.reenlistment_target == 6


def test_noble_skill_tables() -> None:
    assert NOBLE_CAREER.personal_development == (
        "+1 Dex",
        "+1 Int",
        "+1 Edu",
        "+1 Soc",
        "Carousing",
        "Melee Combat",
    )
    assert NOBLE_CAREER.service_skills == (
        "Athletics",
        "Admin",
        "Carousing",
        "Leadership",
        "Gambling",
        "Vehicle",
    )
    assert NOBLE_CAREER.specialist_skills == (
        "Computer",
        "Carousing",
        "Gun Combat",
        "Melee Combat",
        "Liaison",
        "Animals",
    )
    assert NOBLE_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Liaison",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_noble_ranks() -> None:
    assert NOBLE_CAREER.ranks == (
        RankEntry(0, "Courtier", ("Carousing",)),
        RankEntry(1, "Knight", ()),
        RankEntry(2, "Baron", ()),
        RankEntry(3, "Marquis", ()),
        RankEntry(4, "Count", ("Advocate",)),
        RankEntry(5, "Duke", ()),
        RankEntry(6, "Archduke", ()),
    )


def test_noble_benefits() -> None:
    assert NOBLE_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert NOBLE_CAREER.material_benefits == (
        "High Passage",
        "+1 Edu",
        "+1 Int",
        "High Passage",
        "Explorers' Society",
        "High Passage",
        "1D6 Ship Shares",
    )
