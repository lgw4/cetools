import dataclasses
import os

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate_character
from cetools.engine.models import Character, GenerationFailure
from conftest import ConstantRoller, SmartRoller


def test_extensibility_stub_career_returns_character_or_failure() -> None:
    """A non-Navy Career passes through generate_character unchanged."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = SmartRoller(two_dice_value=12, one_die_value=1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, (Character, GenerationFailure))


def test_extensibility_failure_path_with_stub_career() -> None:
    """A stub career with always-low rolls triggers enlistment failure."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = ConstantRoller(1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, GenerationFailure)


def test_extensibility_result_uses_stub_career_name() -> None:
    """Character or failure reason reflects the stub career name, not 'Navy'."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = ConstantRoller(1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, GenerationFailure)
    assert "Scout" in result.reason
    assert "Navy" not in result.reason


def test_extensibility_success_character_career_name() -> None:
    """Successful generation reflects the stub career name."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    roller = SmartRoller(two_dice_value=12, one_die_value=1)
    result = generate_character(stub, roller=roller)
    assert isinstance(result, Character)
    assert result.career == "Scout"


def test_generator_has_no_navy_literal() -> None:
    """No 'Navy' string literal in the engine generator source."""
    generator_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "cetools",
        "engine",
        "generator.py",
    )
    with open(os.path.normpath(generator_path)) as f:
        source = f.read()
    assert '"Navy"' not in source, 'Hardcoded "Navy" found in generator.py'
    assert "'Navy'" not in source, "Hardcoded 'Navy' found in generator.py"


def test_navy_qualification_stat_and_target() -> None:
    assert NAVY_CAREER.qualification_stat == "Intelligence"
    assert NAVY_CAREER.qualification_target == 6


def test_navy_survival_stat_and_target() -> None:
    assert NAVY_CAREER.survival_stat == "Intelligence"
    assert NAVY_CAREER.survival_target == 5


def test_navy_commission_stat_and_target() -> None:
    assert NAVY_CAREER.commission_stat == "Social Standing"
    assert NAVY_CAREER.commission_target == 7


def test_navy_advancement_stat_and_target() -> None:
    assert NAVY_CAREER.advancement_stat == "Education"
    assert NAVY_CAREER.advancement_target == 6


def test_navy_skill_tables_have_six_entries() -> None:
    assert len(NAVY_CAREER.service_skills) == 6
    assert len(NAVY_CAREER.personal_development) == 6
    assert len(NAVY_CAREER.specialist_skills) == 6
    assert len(NAVY_CAREER.advanced_education) == 6


def test_navy_benefit_tables_have_seven_entries() -> None:
    assert len(NAVY_CAREER.cash_benefits) == 7
    assert len(NAVY_CAREER.material_benefits) == 7


def test_navy_service_skills_content() -> None:
    assert NAVY_CAREER.service_skills == (
        "Comms",
        "Engineering",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Vehicle",
    )


def test_navy_rank_titles_match_srd() -> None:
    expected = [
        "Starman",
        "Midshipman",
        "Lieutenant",
        "Lt Commander",
        "Commander",
        "Captain",
        "Commodore",
    ]
    assert len(NAVY_CAREER.ranks) == 7
    for i, title in enumerate(expected):
        assert (
            NAVY_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {NAVY_CAREER.ranks[i].title!r}"


def test_navy_rank_0_grants_zero_g() -> None:
    assert "Zero-G" in NAVY_CAREER.ranks[0].bonus_skills


def test_navy_rank_3_grants_tactics() -> None:
    assert "Tactics" in NAVY_CAREER.ranks[3].bonus_skills


def test_navy_ranks_without_bonus_skills() -> None:
    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            NAVY_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


def test_navy_cash_benefits_values() -> None:
    assert NAVY_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)


def test_navy_material_benefits_content() -> None:
    assert NAVY_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    )


def test_navy_reenlistment_target() -> None:
    assert NAVY_CAREER.reenlistment_target == 5


def test_navy_name() -> None:
    assert NAVY_CAREER.name == "Navy"


from cetools.engine.careers.maritime import MARITIME_CAREER  # noqa: E402
from cetools.engine.careers.registry import CAREER_REGISTRY, DRAFT_TABLE  # noqa: E402

# T003 — SCOUT_CAREER field validation
from cetools.engine.careers.scout import SCOUT_CAREER  # noqa: E402
from cetools.engine.careers.surface import SURFACE_CAREER  # noqa: E402


def test_scout_career_name() -> None:
    assert SCOUT_CAREER.name == "Scout"


def test_scout_qualification_stat_and_target() -> None:
    assert SCOUT_CAREER.qualification_stat == "Intelligence"
    assert SCOUT_CAREER.qualification_target == 6


def test_scout_survival_stat_and_target() -> None:
    assert SCOUT_CAREER.survival_stat == "Endurance"
    assert SCOUT_CAREER.survival_target == 7


def test_scout_no_commission_or_advancement() -> None:
    assert SCOUT_CAREER.commission_stat is None
    assert SCOUT_CAREER.commission_target is None
    assert SCOUT_CAREER.advancement_stat is None
    assert SCOUT_CAREER.advancement_target is None


def test_scout_reenlistment_target() -> None:
    assert SCOUT_CAREER.reenlistment_target == 6


def test_scout_service_skills() -> None:
    assert SCOUT_CAREER.service_skills == (
        "Comms",
        "Electronics",
        "Gun Combat",
        "Gunnery",
        "Recon",
        "Piloting",
    )


def test_scout_personal_development() -> None:
    assert SCOUT_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Jack o' Trades",
        "+1 Edu",
        "Melee Combat",
    )


def test_scout_specialist_skills() -> None:
    assert SCOUT_CAREER.specialist_skills == (
        "Engineering",
        "Gunnery",
        "Demolitions",
        "Navigation",
        "Medicine",
        "Vehicle",
    )


def test_scout_advanced_education() -> None:
    assert SCOUT_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Linguistics",
        "Medicine",
        "Navigation",
        "Tactics",
    )


def test_scout_skill_tables_have_six_entries() -> None:
    assert len(SCOUT_CAREER.service_skills) == 6
    assert len(SCOUT_CAREER.personal_development) == 6
    assert len(SCOUT_CAREER.specialist_skills) == 6
    assert len(SCOUT_CAREER.advanced_education) == 6


def test_scout_rank_entry() -> None:
    from cetools.engine.careers.base import RankEntry

    assert len(SCOUT_CAREER.ranks) == 1
    assert SCOUT_CAREER.ranks[0] == RankEntry(rank=0, title="Scout", bonus_skills=("Piloting",))


def test_scout_cash_benefits() -> None:
    assert SCOUT_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)


def test_scout_material_benefits() -> None:
    assert SCOUT_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "Explorers' Society",
        "Courier Vessel",
    )


def test_scout_cash_benefits_has_seven_entries() -> None:
    assert len(SCOUT_CAREER.cash_benefits) == 7


def test_scout_material_benefits_has_six_entries() -> None:
    assert len(SCOUT_CAREER.material_benefits) == 6


def test_career_registry_has_navy_and_scout_keys() -> None:
    assert "navy" in CAREER_REGISTRY
    assert "scout" in CAREER_REGISTRY


def test_career_registry_navy_value() -> None:
    assert CAREER_REGISTRY["navy"] is NAVY_CAREER


def test_career_registry_scout_value() -> None:
    assert CAREER_REGISTRY["scout"] is SCOUT_CAREER


def test_career_registry_has_maritime_key() -> None:
    assert "maritime system defense" in CAREER_REGISTRY


def test_career_registry_maritime_value() -> None:
    assert CAREER_REGISTRY["maritime system defense"] is MARITIME_CAREER


def test_career_registry_has_surface_key() -> None:
    assert "surface system defense" in CAREER_REGISTRY


def test_career_registry_surface_value() -> None:
    assert CAREER_REGISTRY["surface system defense"] is SURFACE_CAREER


def test_draft_table_length_is_six() -> None:
    assert len(DRAFT_TABLE) == 6


def test_draft_table_index_4_is_scout() -> None:
    assert DRAFT_TABLE[4] == "scout"


def test_draft_table_index_0_is_aerospace() -> None:
    assert DRAFT_TABLE[0] == "aerospace system defense"


def test_draft_table_index_1_is_marine() -> None:
    assert DRAFT_TABLE[1] == "marine"


def test_draft_table_index_2_is_maritime() -> None:
    assert DRAFT_TABLE[2] == "maritime system defense"


def test_draft_table_index_3_is_navy() -> None:
    assert DRAFT_TABLE[3] == "navy"


def test_draft_table_index_5_is_surface() -> None:
    assert DRAFT_TABLE[5] == "surface system defense"


def test_draft_table_only_slot_3_is_navy() -> None:
    for i, entry in enumerate(DRAFT_TABLE):
        if i == 3:
            assert entry == "navy", f"DRAFT_TABLE[3] expected 'navy', got {entry!r}"
        else:
            assert entry != "navy", f"DRAFT_TABLE[{i}] unexpectedly 'navy'"


# ── Career.__post_init__ validation ──────────────────────────────────────────


def _make_valid_career(**overrides):
    """Return a valid Career built from NAVY_CAREER fields with optional overrides."""
    import dataclasses

    from cetools.engine.careers.navy import NAVY_CAREER

    return dataclasses.replace(NAVY_CAREER, **overrides)


def test_career_rejects_invalid_qualification_stat() -> None:
    import pytest

    with pytest.raises(ValueError, match="qualification_stat"):
        _make_valid_career(name="Bad", qualification_stat="Luck")


def test_career_rejects_invalid_survival_stat() -> None:
    import pytest

    with pytest.raises(ValueError, match="survival_stat"):
        _make_valid_career(name="Bad", survival_stat="Luck")


def test_career_rejects_invalid_commission_stat() -> None:
    import pytest

    with pytest.raises(ValueError, match="commission_stat"):
        _make_valid_career(name="Bad", commission_stat="Luck")


def test_career_rejects_invalid_advancement_stat() -> None:
    import pytest

    with pytest.raises(ValueError, match="advancement_stat"):
        _make_valid_career(name="Bad", advancement_stat="Luck")


def test_career_rejects_skill_table_wrong_length() -> None:
    import pytest

    with pytest.raises(ValueError, match="service_skills"):
        _make_valid_career(name="Bad", service_skills=("A", "B"))


def test_career_rejects_too_few_ranks() -> None:
    import pytest

    with pytest.raises(ValueError, match="ranks"):
        _make_valid_career(name="Bad", ranks=())


def test_career_rejects_too_many_ranks() -> None:
    import pytest

    from cetools.engine.careers.base import RankEntry

    eight_ranks = tuple(RankEntry(rank=i, title=f"R{i}", bonus_skills=()) for i in range(8))
    with pytest.raises(ValueError, match="ranks"):
        _make_valid_career(name="Bad", ranks=eight_ranks)


def test_career_rejects_nonconsecutive_ranks() -> None:
    import pytest

    from cetools.engine.careers.base import RankEntry

    bad_ranks = (
        RankEntry(rank=0, title="R0", bonus_skills=()),
        RankEntry(rank=2, title="R2", bonus_skills=()),
    )
    with pytest.raises(ValueError, match="rank at index 1"):
        _make_valid_career(name="Bad", ranks=bad_ranks)


def test_career_allows_none_qualification() -> None:
    career = _make_valid_career(name="NoQual", qualification_stat=None, qualification_target=None)
    assert career.qualification_stat is None
    assert career.qualification_target is None


def test_career_rejects_qualification_stat_none_with_target_set() -> None:
    import pytest

    with pytest.raises(ValueError, match="both be set or both be None"):
        _make_valid_career(name="Bad", qualification_stat=None)


def test_career_rejects_qualification_target_none_with_stat_set() -> None:
    import pytest

    with pytest.raises(ValueError, match="both be set or both be None"):
        _make_valid_career(name="Bad", qualification_target=None)


from cetools.engine.careers.agent import AGENT_CAREER  # noqa: E402
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER  # noqa: E402
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER  # noqa: E402
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER  # noqa: E402
from cetools.engine.careers.noble import NOBLE_CAREER  # noqa: E402


def test_registry_has_social_career_keys() -> None:
    for key in ("agent", "bureaucrat", "diplomat", "entertainer", "noble"):
        assert key in CAREER_REGISTRY


def test_registry_social_career_values() -> None:
    assert CAREER_REGISTRY["agent"] is AGENT_CAREER
    assert CAREER_REGISTRY["bureaucrat"] is BUREAUCRAT_CAREER
    assert CAREER_REGISTRY["diplomat"] is DIPLOMAT_CAREER
    assert CAREER_REGISTRY["entertainer"] is ENTERTAINER_CAREER
    assert CAREER_REGISTRY["noble"] is NOBLE_CAREER


def test_social_careers_not_draftable() -> None:
    for key in ("agent", "bureaucrat", "diplomat", "entertainer", "noble"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


from cetools.engine.careers.athlete import ATHLETE_CAREER  # noqa: E402
from cetools.engine.careers.barbarian import BARBARIAN_CAREER  # noqa: E402
from cetools.engine.careers.colonist import COLONIST_CAREER  # noqa: E402
from cetools.engine.careers.drifter import DRIFTER_CAREER  # noqa: E402
from cetools.engine.careers.hunter import HUNTER_CAREER  # noqa: E402


def test_registry_has_frontier_career_keys() -> None:
    for key in ("athlete", "barbarian", "colonist", "hunter", "drifter"):
        assert key in CAREER_REGISTRY


def test_registry_frontier_career_values() -> None:
    assert CAREER_REGISTRY["athlete"] is ATHLETE_CAREER
    assert CAREER_REGISTRY["barbarian"] is BARBARIAN_CAREER
    assert CAREER_REGISTRY["colonist"] is COLONIST_CAREER
    assert CAREER_REGISTRY["hunter"] is HUNTER_CAREER
    assert CAREER_REGISTRY["drifter"] is DRIFTER_CAREER


def test_frontier_careers_not_draftable() -> None:
    for key in ("athlete", "barbarian", "colonist", "hunter", "drifter"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


from cetools.engine.careers.belter import BELTER_CAREER  # noqa: E402
from cetools.engine.careers.mercenary import MERCENARY_CAREER  # noqa: E402
from cetools.engine.careers.merchant import MERCHANT_CAREER  # noqa: E402
from cetools.engine.careers.pirate import PIRATE_CAREER  # noqa: E402
from cetools.engine.careers.rogue import ROGUE_CAREER  # noqa: E402


def test_registry_has_rogue_spacer_career_keys() -> None:
    for key in ("belter", "mercenary", "pirate", "rogue", "merchant"):
        assert key in CAREER_REGISTRY


def test_registry_rogue_spacer_career_values() -> None:
    assert CAREER_REGISTRY["belter"] is BELTER_CAREER
    assert CAREER_REGISTRY["mercenary"] is MERCENARY_CAREER
    assert CAREER_REGISTRY["pirate"] is PIRATE_CAREER
    assert CAREER_REGISTRY["rogue"] is ROGUE_CAREER
    assert CAREER_REGISTRY["merchant"] is MERCHANT_CAREER


def test_rogue_spacer_careers_not_draftable() -> None:
    for key in ("belter", "mercenary", "pirate", "rogue", "merchant"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


from cetools.engine.careers.physician import PHYSICIAN_CAREER  # noqa: E402
from cetools.engine.careers.scientist import SCIENTIST_CAREER  # noqa: E402
from cetools.engine.careers.technician import TECHNICIAN_CAREER  # noqa: E402


def test_registry_has_learned_career_keys() -> None:
    for key in ("physician", "scientist", "technician"):
        assert key in CAREER_REGISTRY


def test_registry_learned_career_values() -> None:
    assert CAREER_REGISTRY["physician"] is PHYSICIAN_CAREER
    assert CAREER_REGISTRY["scientist"] is SCIENTIST_CAREER
    assert CAREER_REGISTRY["technician"] is TECHNICIAN_CAREER


def test_learned_careers_not_draftable() -> None:
    for key in ("physician", "scientist", "technician"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


def test_registry_has_all_24_careers() -> None:
    assert len(CAREER_REGISTRY) == 24
