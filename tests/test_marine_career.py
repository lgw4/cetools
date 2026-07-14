from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.generator import generate
from cetools.engine.models import Character
from cetools.engine.rolls import RandomRolls, RollName, ScriptedRolls

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


# --- T007A: statistical stability over 100 runs with real dice ---


def test_generate_career_character_marine_100_runs_no_unhandled_exceptions() -> None:
    for _ in range(100):
        result = generate(MARINE_CAREER, RandomRolls())
        assert isinstance(result, Character)
        assert result.career.name == "Marine"
        assert result.rank_title in _MARINE_RANK_TITLES


# ---------------------------------------------------------------------------
# US2 (Phase 4): commission, advancement, rank cap, bonus-skill retention,
# rank-based mustering-out bonus rolls
# ---------------------------------------------------------------------------


# Every characteristic rolls 7: every characteristic_modifier is 0, Education 7
# keeps the Advanced Education skill table out of play, and 7 clears the Marine
# qualification target on the first try.
_FLAT_CHARACTERISTICS = 7


# --- T013: commission roll success/failure at rank 0 ---


def test_marine_commission_success_advances_rank_0_to_1() -> None:
    # Survive, commission (→ rank 1), then fail the advancement roll that a
    # fresh commission triggers, so the character holds at rank 1. A
    # reenlistment of 2 (below the target of 6) ends the career after one term.
    rolls = ScriptedRolls(
        checks={
            RollName.SURVIVAL: True,
            RollName.COMMISSION: True,
            RollName.ADVANCEMENT: False,
        },
        two_d6={
            RollName.CHARACTERISTIC: _FLAT_CHARACTERISTICS,
            RollName.REENLISTMENT: 2,
        },
    )
    result = generate(MARINE_CAREER, rolls)
    assert isinstance(result, Character)
    assert result.rank == 1
    assert result.rank_title == "Lieutenant"
    term = result.terms[0]
    assert term.commissioned is True
    assert len(term.skills_gained[6:]) == 1, "a commissioned term grants exactly 1 skill roll"


def test_marine_commission_failure_stays_rank_0() -> None:
    # Survive, then fail the commission: the character stays rank 0 and never
    # reaches an advancement roll, which is only attempted once commissioned.
    # A reenlistment of 2 (below the target of 6) ends the career after one term.
    rolls = ScriptedRolls(
        checks={RollName.SURVIVAL: True, RollName.COMMISSION: False},
        two_d6={
            RollName.CHARACTERISTIC: _FLAT_CHARACTERISTICS,
            RollName.REENLISTMENT: 2,
        },
    )
    result = generate(MARINE_CAREER, rolls)
    assert isinstance(result, Character)
    assert result.rank == 0
    assert result.rank_title == "Trooper"


# --- T014: advancement roll increments a commissioned officer's rank ---


def test_marine_advancement_increments_commissioned_officer_rank() -> None:
    # Term 1: survive, commission (→ rank 1), fail the advancement that follows
    # the commission; reenlist with 8 (≥ 6) to serve a second term.
    # Term 2: already an officer, so no commission is attempted; survive and
    # pass advancement → rank 2. Reenlist with 2 (< 6) → stop.
    rolls = ScriptedRolls(
        checks={
            RollName.SURVIVAL: True,
            RollName.COMMISSION: True,
            RollName.ADVANCEMENT: [False, True],
        },
        two_d6={
            RollName.CHARACTERISTIC: _FLAT_CHARACTERISTICS,
            RollName.REENLISTMENT: [8, 2],
        },
    )
    result = generate(MARINE_CAREER, rolls)
    assert isinstance(result, Character)
    assert result.rank == 2
    assert result.rank_title == "Captain"
    assert result.terms[1].promoted is True


# --- T015: rank cap at 6 (Brigadier) ---


def _maximal_career_rolls() -> ScriptedRolls:
    """Every check passes and every reenlistment succeeds: a full 7-term career.

    Commission fires in term 1 and advancement every term after, so rank climbs
    0→2 in term 1 and +1 per term until it hits the cap. Every characteristic is
    7, which clears the qualification target on the first roll.
    """
    return ScriptedRolls(
        checks={
            RollName.SURVIVAL: True,
            RollName.COMMISSION: True,
            RollName.ADVANCEMENT: True,
        },
        two_d6={
            RollName.CHARACTERISTIC: _FLAT_CHARACTERISTICS,
            RollName.REENLISTMENT: 8,  # ≥ the target of 6
        },
    )


def test_marine_rank_capped_at_6() -> None:
    # Rank reaches the cap by term 5 and must hold there through term 7.
    result = generate(MARINE_CAREER, _maximal_career_rolls())
    assert isinstance(result, Character)
    assert result.rank == 6
    assert result.rank_title == "Brigadier"


# --- T016: rank-0 and rank-3 bonus skills applied and retained ---


def test_marine_rank_0_zero_g_applied_at_enlistment() -> None:
    result = generate(MARINE_CAREER, _maximal_career_rolls())
    assert isinstance(result, Character)
    assert result.skills.get("Zero-G") == 1, "rank-0 bonus should grant Zero-G-1"


def test_marine_rank_3_tactics_applied() -> None:
    result = generate(MARINE_CAREER, _maximal_career_rolls())
    assert isinstance(result, Character)
    assert result.rank >= 3
    assert result.skills.get("Tactics") == 1, "rank-3 bonus should grant Tactics-1"


def test_marine_commissioned_officer_retains_rank_0_zero_g_bonus() -> None:
    # Same rolls as test_marine_commission_success_advances_rank_0_to_1:
    # commissioned to rank 1, never demoted — the rank-0 Zero-G bonus must
    # persist since skills accumulate and are never cleared.
    rolls = ScriptedRolls(
        checks={
            RollName.SURVIVAL: True,
            RollName.COMMISSION: True,
            RollName.ADVANCEMENT: False,
        },
        two_d6={
            RollName.CHARACTERISTIC: _FLAT_CHARACTERISTICS,
            RollName.REENLISTMENT: 2,
        },
    )
    result = generate(MARINE_CAREER, rolls)
    assert isinstance(result, Character)
    assert result.rank == 1
    assert result.skills.get("Zero-G") == 1


# --- T017: rank-based bonus mustering-out rolls (FR-011) ---


def test_marine_rank_6_bonus_muster_rolls_applied() -> None:
    # A maximal career reaches rank 6 (Brigadier) over 7 terms (see
    # test_marine_rank_capped_at_6). Rank 6 grants +3 bonus mustering-out
    # rolls on top of the 1-per-term-served baseline (7 + 3 = 10).
    result = generate(MARINE_CAREER, _maximal_career_rolls())
    assert isinstance(result, Character)
    assert result.rank == 6
    assert result.terms_served == 7
    expected_total = result.terms_served + 3
    assert len(result.benefits) == expected_total
