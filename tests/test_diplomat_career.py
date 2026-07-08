from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER


def test_diplomat_scalar_fields() -> None:
    assert DIPLOMAT_CAREER.name == "Diplomat"
    assert DIPLOMAT_CAREER.qualification_stat == "Social Standing"
    assert DIPLOMAT_CAREER.qualification_target == 6
    assert DIPLOMAT_CAREER.survival_stat == "Education"
    assert DIPLOMAT_CAREER.survival_target == 5
    assert DIPLOMAT_CAREER.commission_stat == "Intelligence"
    assert DIPLOMAT_CAREER.commission_target == 7
    assert DIPLOMAT_CAREER.advancement_stat == "Social Standing"
    assert DIPLOMAT_CAREER.advancement_target == 7
    assert DIPLOMAT_CAREER.reenlistment_target == 5


def test_diplomat_skill_tables() -> None:
    assert DIPLOMAT_CAREER.personal_development == (
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Athletics",
        "Carousing",
    )
    assert DIPLOMAT_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Carousing",
        "Bribery",
        "Liaison",
        "Vehicle",
    )
    assert DIPLOMAT_CAREER.specialist_skills == (
        "Carousing",
        "Linguistics",
        "Bribery",
        "Liaison",
        "Steward",
        "Vehicle",
    )
    assert DIPLOMAT_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Liaison",
        "Linguistics",
        "Medicine",
        "Leadership",
    )


def test_diplomat_ranks() -> None:
    assert DIPLOMAT_CAREER.ranks == (
        RankEntry(0, "Attaché", ("Liaison",)),
        RankEntry(1, "Third Secretary", ()),
        RankEntry(2, "Second Secretary", ()),
        RankEntry(3, "First Secretary", ("Admin",)),
        RankEntry(4, "Counselor", ()),
        RankEntry(5, "Minister", ()),
        RankEntry(6, "Ambassador", ()),
    )


def test_diplomat_benefits() -> None:
    assert DIPLOMAT_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert DIPLOMAT_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    )
