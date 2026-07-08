from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.base import RankEntry


def test_agent_scalar_fields() -> None:
    assert AGENT_CAREER.name == "Agent"
    assert AGENT_CAREER.qualification_stat == "Social Standing"
    assert AGENT_CAREER.qualification_target == 6
    assert AGENT_CAREER.survival_stat == "Intelligence"
    assert AGENT_CAREER.survival_target == 6
    assert AGENT_CAREER.commission_stat == "Education"
    assert AGENT_CAREER.commission_target == 7
    assert AGENT_CAREER.advancement_stat == "Education"
    assert AGENT_CAREER.advancement_target == 6
    assert AGENT_CAREER.reenlistment_target == 6


def test_agent_skill_tables() -> None:
    assert AGENT_CAREER.personal_development == (
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Athletics",
        "Carousing",
    )
    assert AGENT_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Streetwise",
        "Bribery",
        "Leadership",
        "Vehicle",
    )
    assert AGENT_CAREER.specialist_skills == (
        "Gun Combat",
        "Melee Combat",
        "Bribery",
        "Leadership",
        "Recon",
        "Survival",
    )
    assert AGENT_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Liaison",
        "Linguistics",
        "Medicine",
        "Leadership",
    )


def test_agent_ranks() -> None:
    assert AGENT_CAREER.ranks == (
        RankEntry(0, "Agent", ("Streetwise",)),
        RankEntry(1, "Special Agent", ()),
        RankEntry(2, "Sp Agent in Charge", ()),
        RankEntry(3, "Unit Chief", ()),
        RankEntry(4, "Section Chief", ("Admin",)),
        RankEntry(5, "Assistant Director", ()),
        RankEntry(6, "Director", ()),
    )


def test_agent_benefits() -> None:
    assert AGENT_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert AGENT_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    )
