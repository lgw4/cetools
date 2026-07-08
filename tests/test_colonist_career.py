from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.colonist import COLONIST_CAREER


def test_colonist_scalar_fields() -> None:
    assert COLONIST_CAREER.name == "Colonist"
    assert COLONIST_CAREER.qualification_stat == "Endurance"
    assert COLONIST_CAREER.qualification_target == 5
    assert COLONIST_CAREER.survival_stat == "Endurance"
    assert COLONIST_CAREER.survival_target == 6
    assert COLONIST_CAREER.commission_stat == "Intelligence"
    assert COLONIST_CAREER.commission_target == 7
    assert COLONIST_CAREER.advancement_stat == "Education"
    assert COLONIST_CAREER.advancement_target == 6
    assert COLONIST_CAREER.reenlistment_target == 5


def test_colonist_skill_tables() -> None:
    assert COLONIST_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "Athletics",
        "Gun Combat",
    )
    assert COLONIST_CAREER.service_skills == (
        "Mechanics",
        "Gun Combat",
        "Animals",
        "Electronics",
        "Survival",
        "Vehicle",
    )
    assert COLONIST_CAREER.specialist_skills == (
        "Athletics",
        "Carousing",
        "Jack o' Trades",
        "Engineering",
        "Animals",
        "Vehicle",
    )
    assert COLONIST_CAREER.advanced_education == (
        "Advocate",
        "Linguistics",
        "Medicine",
        "Liaison",
        "Admin",
        "Animals",
    )


def test_colonist_ranks() -> None:
    assert COLONIST_CAREER.ranks == (
        RankEntry(0, "Citizen", ("Survival",)),
        RankEntry(1, "District Leader", ()),
        RankEntry(2, "District Delegate", ()),
        RankEntry(3, "Council Advisor", ("Liaison",)),
        RankEntry(4, "Councilor", ()),
        RankEntry(5, "Lieutenant Governor", ()),
        RankEntry(6, "Governor", ()),
    )


def test_colonist_benefits() -> None:
    assert COLONIST_CAREER.cash_benefits == (1000, 5000, 5000, 5000, 10000, 20000, 50000)
    assert COLONIST_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
    )
