from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.dice import RandomDiceRoller
from cetools.engine.generator import generate_career_character, generate_character
from cetools.engine.models import Character
from conftest import SequenceRoller, SmartRoller

_MARINE_RANK_TITLES = {
    "Trooper",
    "Lieutenant",
    "Captain",
    "Major",
    "Lt Colonel",
    "Colonel",
    "Brigadier",
}


# --- T002: qualification, survival, commission, advancement, reenlistment, name ---


def test_marine_name() -> None:
    assert MARINE_CAREER.name == "Marine"


def test_marine_qualification_stat_and_target() -> None:
    assert MARINE_CAREER.qualification_stat == "Intelligence"
    assert MARINE_CAREER.qualification_target == 6


def test_marine_survival_stat_and_target() -> None:
    assert MARINE_CAREER.survival_stat == "Endurance"
    assert MARINE_CAREER.survival_target == 6


def test_marine_commission_stat_and_target() -> None:
    assert MARINE_CAREER.commission_stat == "Education"
    assert MARINE_CAREER.commission_target == 6


def test_marine_advancement_stat_and_target() -> None:
    assert MARINE_CAREER.advancement_stat == "Social Standing"
    assert MARINE_CAREER.advancement_target == 7


def test_marine_reenlistment_target() -> None:
    assert MARINE_CAREER.reenlistment_target == 6


# --- T003: skill tables (24 positions across 4 tables) ---


def test_marine_personal_development_table() -> None:
    assert MARINE_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Melee Combat",
    )


def test_marine_service_skills_table() -> None:
    assert MARINE_CAREER.service_skills == (
        "Comms",
        "Demolitions",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Battle Dress",
    )


def test_marine_specialist_skills_table() -> None:
    assert MARINE_CAREER.specialist_skills == (
        "Electronics",
        "Gun Combat",
        "Melee Combat",
        "Survival",
        "Recon",
        "Vehicle",
    )


def test_marine_advanced_education_table() -> None:
    assert MARINE_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Gravitics",
        "Medicine",
        "Navigation",
        "Tactics",
    )


def test_marine_skill_tables_have_six_entries() -> None:
    assert len(MARINE_CAREER.personal_development) == 6
    assert len(MARINE_CAREER.service_skills) == 6
    assert len(MARINE_CAREER.specialist_skills) == 6
    assert len(MARINE_CAREER.advanced_education) == 6


# --- T004: seven rank entries (rank 0 Trooper through rank 6 Brigadier) ---


def test_marine_rank_titles_match_srd() -> None:
    expected = [
        "Trooper",
        "Lieutenant",
        "Captain",
        "Major",
        "Lt Colonel",
        "Colonel",
        "Brigadier",
    ]
    assert len(MARINE_CAREER.ranks) == 7
    for i, title in enumerate(expected):
        assert (
            MARINE_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {MARINE_CAREER.ranks[i].title!r}"


def test_marine_rank_0_grants_zero_g() -> None:
    assert MARINE_CAREER.ranks[0].bonus_skills == ("Zero-G",)


def test_marine_rank_3_grants_tactics() -> None:
    assert MARINE_CAREER.ranks[3].bonus_skills == ("Tactics",)


def test_marine_ranks_without_bonus_skills() -> None:
    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            MARINE_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


# --- T005: mustering-out tables — 7 cash entries, 7 material entries ---


def test_marine_cash_benefits_values() -> None:
    assert MARINE_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)


def test_marine_material_benefits_content() -> None:
    assert MARINE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    )


def test_marine_material_benefit_explorers_society_spelling() -> None:
    assert MARINE_CAREER.material_benefits[6] == "Explorers' Society"


def test_marine_benefit_tables_have_seven_entries() -> None:
    assert len(MARINE_CAREER.cash_benefits) == 7
    assert len(MARINE_CAREER.material_benefits) == 7


# --- T007A: statistical stability over 100 runs with RandomDiceRoller ---


def test_generate_career_character_marine_100_runs_no_unhandled_exceptions() -> None:
    for _ in range(100):
        result = generate_career_character(MARINE_CAREER, roller=RandomDiceRoller())
        assert isinstance(result, Character)
        assert result.career == "Marine"
        assert result.rank_title in _MARINE_RANK_TITLES


# ---------------------------------------------------------------------------
# US2 (Phase 4): commission, advancement, rank cap, bonus-skill retention,
# rank-based mustering-out bonus rolls
# ---------------------------------------------------------------------------


# All stats = 7 → characteristic_modifier(7) = 0 for every check, so each 2D6
# roll below can be reasoned about against the raw target number.
_PRESET = {
    "Strength": 7,
    "Dexterity": 7,
    "Endurance": 7,
    "Intelligence": 7,
    "Education": 7,
    "Social Standing": 7,
}


# --- T013: commission roll success/failure at rank 0 ---


def test_marine_commission_success_advances_rank_0_to_1() -> None:
    # Survival (End 6, dm0): 8 ✓. Commission (Edu 6, dm0): 6 ✓ → rank 1.
    # Advancement (Soc 7, dm0), rolled immediately on commission: 2 ✗ → stays rank 1.
    # Commissioned this term → exactly 1 skill roll (table, entry).
    # Reenlistment (target 6): 2 ✗ → stop after 1 term.
    roller = SequenceRoller([6, 6, 6] + [8, 6, 2, 1, 1, 2], default=1)
    result = generate_character(
        MARINE_CAREER,
        roller=roller,
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 1
    assert result.rank_title == "Lieutenant"
    term = result.terms[0]
    assert term.commissioned is True
    assert len(term.skills_gained[6:]) == 1, "a commissioned term grants exactly 1 skill roll"


def test_marine_commission_failure_stays_rank_0() -> None:
    # Survival: 8 ✓. Commission: 2 ✗ → stays rank 0 (never reaches the
    # advancement roll, which is only attempted after a successful commission).
    # Not commissioned/promoted this term → 2 skill rolls (table, entry) x2.
    # Reenlistment: 2 ✗ → stop after 1 term.
    roller = SequenceRoller([6, 6, 6] + [8, 2, 1, 1, 1, 1, 2], default=1)
    result = generate_character(
        MARINE_CAREER,
        roller=roller,
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 0
    assert result.rank_title == "Trooper"


# --- T014: advancement roll increments a commissioned officer's rank ---


def test_marine_advancement_increments_commissioned_officer_rank() -> None:
    # Term 1: survival 8 ✓, commission 6 ✓ → rank 1; advancement 2 ✗ → stays
    # rank 1; 1 skill roll; reenlist 8 (≥6) → continue.
    # Term 2 (rank 1, no further commission attempt): survival 8 ✓;
    # advancement 8 ✓ (≥7) → rank 2; 1 skill roll; reenlist 2 ✗ → stop.
    roller = SequenceRoller([6, 6, 6] + [8, 6, 2, 1, 1, 8, 8, 8, 1, 1, 2], default=1)
    result = generate_character(
        MARINE_CAREER,
        roller=roller,
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 2
    assert result.rank_title == "Captain"
    assert result.terms[1].promoted is True


# --- T015: rank cap at 6 (Brigadier) ---


def test_marine_rank_capped_at_6() -> None:
    # SmartRoller(10, 1): every 2D6 check passes (Marine's highest target is
    # 7), so commission + advancement fire every eligible term. Rank climbs
    # 0→2 in term 1 (commission then advancement) and +1 per subsequent term,
    # reaching the rank-6 cap by term 5 and holding there through term 7.
    result = generate_character(MARINE_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.rank == 6
    assert result.rank_title == "Brigadier"


# --- T016: rank-0 and rank-3 bonus skills applied and retained ---


def test_marine_rank_0_zero_g_applied_at_enlistment() -> None:
    result = generate_character(MARINE_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.skills.get("Zero-G") == 1, "rank-0 bonus should grant Zero-G-1"


def test_marine_rank_3_tactics_applied() -> None:
    result = generate_character(MARINE_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.rank >= 3
    assert result.skills.get("Tactics") == 1, "rank-3 bonus should grant Tactics-1"


def test_marine_commissioned_officer_retains_rank_0_zero_g_bonus() -> None:
    # Same script as test_marine_commission_success_advances_rank_0_to_1:
    # commissioned to rank 1, never demoted — the rank-0 Zero-G bonus must
    # persist since skills accumulate and are never cleared.
    roller = SequenceRoller([6, 6, 6] + [8, 6, 2, 1, 1, 2], default=1)
    result = generate_character(
        MARINE_CAREER,
        roller=roller,
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 1
    assert result.skills.get("Zero-G") == 1


# --- T017: rank-based bonus mustering-out rolls (FR-011) ---


def test_marine_rank_6_bonus_muster_rolls_applied() -> None:
    # SmartRoller(10, 1) reaches rank 6 (Brigadier) over 7 terms (see
    # test_marine_rank_capped_at_6). Rank 6 grants +3 bonus mustering-out
    # rolls on top of the 1-per-term-served baseline (7 + 3 = 10).
    result = generate_character(MARINE_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.rank == 6
    assert result.terms_served == 7
    expected_total = result.terms_served + 3
    assert len(result.benefits) == expected_total
