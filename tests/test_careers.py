import dataclasses
import os

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate
from cetools.engine.models import Character, GenerationFailure
from cetools.engine.rolls import RollName, ScriptedRolls
from cetools.engine.rules import SRD


def test_extensibility_stub_career_returns_character_or_failure() -> None:
    """A non-Navy Career passes through generate unchanged."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    result = generate(stub, ScriptedRolls())
    assert isinstance(result, (Character, GenerationFailure))


def test_extensibility_failure_path_with_stub_career() -> None:
    """A stub career whose qualification check fails triggers enlistment failure."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    # Only SRD rules make an enlistment check at all: under HOUSE rules the
    # characteristics are rerolled until they qualify and enlistment cannot fail.
    rolls = ScriptedRolls(checks={RollName.QUALIFICATION: False})
    result = generate(stub, rolls, rules=SRD)
    assert isinstance(result, GenerationFailure)


def test_extensibility_result_uses_stub_career_name() -> None:
    """Character or failure reason reflects the stub career name, not 'Navy'."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    rolls = ScriptedRolls(checks={RollName.QUALIFICATION: False})
    result = generate(stub, rolls, rules=SRD)
    assert isinstance(result, GenerationFailure)
    assert "Scout" in result.reason
    assert "Navy" not in result.reason


def test_extensibility_success_character_career_name() -> None:
    """Successful generation reflects the stub career name."""
    stub = dataclasses.replace(NAVY_CAREER, name="Scout")
    # Default checks all pass, so survival succeeds and the run always ends in a
    # Character.
    result = generate(stub, ScriptedRolls())
    assert isinstance(result, Character)
    assert result.career.name == "Scout"


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


from cetools.engine.careers.aerospace import AEROSPACE_CAREER  # noqa: E402
from cetools.engine.careers.marine import MARINE_CAREER  # noqa: E402
from cetools.engine.careers.maritime import MARITIME_CAREER  # noqa: E402
from cetools.engine.careers.registry import (  # noqa: E402
    CAREERS,
    DRAFT_TABLE,
    UnknownCareer,
    is_military,
    resolve,
)

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
    assert resolve("navy") is NAVY_CAREER
    assert resolve("scout") is SCOUT_CAREER


def test_career_registry_navy_value() -> None:
    assert resolve("navy") is NAVY_CAREER


def test_career_registry_scout_value() -> None:
    assert resolve("scout") is SCOUT_CAREER


def test_career_registry_has_maritime_key() -> None:
    assert resolve("maritime system defense") is MARITIME_CAREER


def test_career_registry_maritime_value() -> None:
    assert resolve("maritime system defense") is MARITIME_CAREER


def test_career_registry_has_surface_key() -> None:
    assert resolve("surface system defense") is SURFACE_CAREER


def test_career_registry_surface_value() -> None:
    assert resolve("surface system defense") is SURFACE_CAREER


def test_draft_table_length_is_six() -> None:
    assert len(DRAFT_TABLE) == 6


def test_draft_table_index_4_is_scout() -> None:
    assert DRAFT_TABLE[4] is SCOUT_CAREER


def test_draft_table_index_0_is_aerospace() -> None:
    assert DRAFT_TABLE[0] is AEROSPACE_CAREER


def test_draft_table_index_1_is_marine() -> None:
    assert DRAFT_TABLE[1] is MARINE_CAREER


def test_draft_table_index_2_is_maritime() -> None:
    assert DRAFT_TABLE[2] is MARITIME_CAREER


def test_draft_table_index_3_is_navy() -> None:
    assert DRAFT_TABLE[3] is NAVY_CAREER


def test_draft_table_index_5_is_surface() -> None:
    assert DRAFT_TABLE[5] is SURFACE_CAREER


def test_draft_table_only_slot_3_is_navy() -> None:
    for i, entry in enumerate(DRAFT_TABLE):
        if i == 3:
            assert entry is NAVY_CAREER, f"DRAFT_TABLE[3] expected Navy, got {entry.name!r}"
        else:
            assert entry is not NAVY_CAREER, f"DRAFT_TABLE[{i}] unexpectedly Navy"


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
        assert not isinstance(resolve(key), UnknownCareer)


def test_registry_social_career_values() -> None:
    assert resolve("agent") is AGENT_CAREER
    assert resolve("bureaucrat") is BUREAUCRAT_CAREER
    assert resolve("diplomat") is DIPLOMAT_CAREER
    assert resolve("entertainer") is ENTERTAINER_CAREER
    assert resolve("noble") is NOBLE_CAREER


def test_social_careers_not_draftable() -> None:
    for key in ("agent", "bureaucrat", "diplomat", "entertainer", "noble"):
        assert resolve(key) not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


from cetools.engine.careers.athlete import ATHLETE_CAREER  # noqa: E402
from cetools.engine.careers.barbarian import BARBARIAN_CAREER  # noqa: E402
from cetools.engine.careers.colonist import COLONIST_CAREER  # noqa: E402
from cetools.engine.careers.drifter import DRIFTER_CAREER  # noqa: E402
from cetools.engine.careers.hunter import HUNTER_CAREER  # noqa: E402


def test_registry_has_frontier_career_keys() -> None:
    for key in ("athlete", "barbarian", "colonist", "hunter", "drifter"):
        assert not isinstance(resolve(key), UnknownCareer)


def test_registry_frontier_career_values() -> None:
    assert resolve("athlete") is ATHLETE_CAREER
    assert resolve("barbarian") is BARBARIAN_CAREER
    assert resolve("colonist") is COLONIST_CAREER
    assert resolve("hunter") is HUNTER_CAREER
    assert resolve("drifter") is DRIFTER_CAREER


def test_frontier_careers_not_draftable() -> None:
    for key in ("athlete", "barbarian", "colonist", "hunter", "drifter"):
        assert resolve(key) not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


from cetools.engine.careers.belter import BELTER_CAREER  # noqa: E402
from cetools.engine.careers.mercenary import MERCENARY_CAREER  # noqa: E402
from cetools.engine.careers.merchant import MERCHANT_CAREER  # noqa: E402
from cetools.engine.careers.pirate import PIRATE_CAREER  # noqa: E402
from cetools.engine.careers.rogue import ROGUE_CAREER  # noqa: E402


def test_registry_has_rogue_spacer_career_keys() -> None:
    for key in ("belter", "mercenary", "pirate", "rogue", "merchant"):
        assert not isinstance(resolve(key), UnknownCareer)


def test_registry_rogue_spacer_career_values() -> None:
    assert resolve("belter") is BELTER_CAREER
    assert resolve("mercenary") is MERCENARY_CAREER
    assert resolve("pirate") is PIRATE_CAREER
    assert resolve("rogue") is ROGUE_CAREER
    assert resolve("merchant") is MERCHANT_CAREER


def test_rogue_spacer_careers_not_draftable() -> None:
    for key in ("belter", "mercenary", "pirate", "rogue", "merchant"):
        assert resolve(key) not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


from cetools.engine.careers.physician import PHYSICIAN_CAREER  # noqa: E402
from cetools.engine.careers.scientist import SCIENTIST_CAREER  # noqa: E402
from cetools.engine.careers.technician import TECHNICIAN_CAREER  # noqa: E402


def test_registry_has_learned_career_keys() -> None:
    for key in ("physician", "scientist", "technician"):
        assert not isinstance(resolve(key), UnknownCareer)


def test_registry_learned_career_values() -> None:
    assert resolve("physician") is PHYSICIAN_CAREER
    assert resolve("scientist") is SCIENTIST_CAREER
    assert resolve("technician") is TECHNICIAN_CAREER


def test_learned_careers_not_draftable() -> None:
    for key in ("physician", "scientist", "technician"):
        assert resolve(key) not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


def test_registry_has_all_24_careers() -> None:
    assert len(CAREERS) == 24


# ── resolve() ────────────────────────────────────────────────────────────────


def test_resolve_exact_lowercase_name() -> None:
    assert resolve("navy") is NAVY_CAREER


def test_resolve_mixed_case_name() -> None:
    assert resolve("NaVy") is NAVY_CAREER
    assert resolve("Aerospace System Defense") is AEROSPACE_CAREER


def test_resolve_ignores_surrounding_whitespace() -> None:
    assert resolve("  scout  ") is SCOUT_CAREER
    assert resolve("\tmaritime system defense\n") is MARITIME_CAREER


def test_resolve_reads_hyphens_as_spaces() -> None:
    assert resolve("Aerospace-System-Defense") is AEROSPACE_CAREER
    assert resolve("surface-system-defense") is SURFACE_CAREER


def test_resolve_every_career_by_its_own_name() -> None:
    for career in CAREERS:
        assert resolve(career.name) is career


def test_resolve_near_miss_returns_unknown_with_suggestion() -> None:
    result = resolve("nvy")
    assert isinstance(result, UnknownCareer)
    assert result.suggestion is NAVY_CAREER


def test_resolve_gibberish_returns_unknown_without_suggestion() -> None:
    result = resolve("xyzzy")
    assert isinstance(result, UnknownCareer)
    assert result.suggestion is None


def test_resolve_unknown_preserves_original_spec() -> None:
    result = resolve("  Smuggler-Prince  ")
    assert isinstance(result, UnknownCareer)
    assert result.spec == "  Smuggler-Prince  "


# ── is_military() ────────────────────────────────────────────────────────────


def test_is_military_true_for_every_draft_table_career() -> None:
    for career in DRAFT_TABLE:
        assert is_military(career), f"{career.name} should be military"


def test_is_military_false_for_civilian_careers() -> None:
    assert not is_military(ROGUE_CAREER)
    assert not is_military(MERCHANT_CAREER)


def test_is_military_true_for_exactly_the_six_draft_careers() -> None:
    military = [career for career in CAREERS if is_military(career)]
    assert len(military) == 6
    assert set(military) == set(DRAFT_TABLE)


# ── CAREERS / DRAFT_TABLE shape ──────────────────────────────────────────────


def test_draft_table_has_six_entries_all_in_careers() -> None:
    assert len(DRAFT_TABLE) == 6
    for career in DRAFT_TABLE:
        assert career in CAREERS


def test_careers_holds_all_24_in_name_order() -> None:
    assert len(CAREERS) == 24
    names = [career.name for career in CAREERS]
    assert names == sorted(names)
