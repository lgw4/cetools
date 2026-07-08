from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.belter import BELTER_CAREER


def test_belter_scalar_fields() -> None:
    assert BELTER_CAREER.name == "Belter"
    assert BELTER_CAREER.qualification_stat == "Intelligence"
    assert BELTER_CAREER.qualification_target == 4
    assert BELTER_CAREER.survival_stat == "Dexterity"
    assert BELTER_CAREER.survival_target == 7
    assert BELTER_CAREER.commission_stat is None
    assert BELTER_CAREER.commission_target is None
    assert BELTER_CAREER.advancement_stat is None
    assert BELTER_CAREER.advancement_target is None
    assert BELTER_CAREER.reenlistment_target == 5


def test_belter_skill_tables() -> None:
    assert BELTER_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Zero-G",
        "Melee Combat",
        "Gambling",
    )
    assert BELTER_CAREER.service_skills == (
        "Comms",
        "Demolitions",
        "Gun Combat",
        "Gunnery",
        "Prospecting",
        "Piloting",
    )
    assert BELTER_CAREER.specialist_skills == (
        "Zero-G",
        "Electronics",
        "Prospecting",
        "Sciences",
        "Vehicle",
        "Vehicle",
    )
    assert BELTER_CAREER.advanced_education == (
        "Advocate",
        "Engineering",
        "Medicine",
        "Navigation",
        "Comms",
        "Tactics",
    )


def test_belter_ranks() -> None:
    assert BELTER_CAREER.ranks == (RankEntry(0, "Belter", ()),)


def test_belter_benefits() -> None:
    assert BELTER_CAREER.cash_benefits == (1000, 5000, 5000, 5000, 10000, 20000, 50000)
    assert BELTER_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "1D6 Ship Shares",
        "High Passage",
    )
