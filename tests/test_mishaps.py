from collections import Counter

from cetools.engine.mishaps import (
    INJURY_TABLE,
    SURVIVAL_MISHAPS_TABLE,
    InjuryEntry,
    MishapEntry,
    resolve_survival_mishap,
)
from cetools.engine.rolls import RandomRolls, RollName, ScriptedRolls

# --- T004: table shape ---


def test_survival_mishaps_table_has_six_entries() -> None:
    assert len(SURVIVAL_MISHAPS_TABLE) == 6


def test_injury_table_has_six_entries() -> None:
    assert len(INJURY_TABLE) == 6


def test_survival_mishaps_table_rows_match_data_model() -> None:
    expected = {
        1: ("none", False, 0, 2),
        2: ("honorable", False, 0, 0),
        3: ("honorable", False, 10_000, 0),
        4: ("dishonorable", False, 0, 0),
        5: ("dishonorable", True, 0, 0),
        6: ("medical", False, 0, 1),
    }
    for roll, (discharge_type, imprisoned, debt, injury_rolls) in expected.items():
        entry = SURVIVAL_MISHAPS_TABLE[roll - 1]
        assert isinstance(entry, MishapEntry)
        assert entry.discharge_type == discharge_type
        assert entry.imprisoned == imprisoned
        assert entry.debt == debt
        assert entry.injury_rolls == injury_rolls


def test_injury_table_rows_match_data_model() -> None:
    expected = {
        1: (("Strength", "Dexterity", "Endurance"), 1, 0, 2),
        2: (("Strength", "Dexterity", "Endurance"), 1, 0, 0),
        3: (("Strength", "Dexterity"), 0, 2, 0),
        4: (("Strength", "Dexterity", "Endurance"), 0, 2, 0),
        5: (("Strength", "Dexterity", "Endurance"), 0, 1, 0),
        6: ((), 0, 0, 0),
    }
    for roll, (candidate_stats, primary_dice, primary_fixed, secondary_amount) in expected.items():
        entry = INJURY_TABLE[roll - 1]
        assert isinstance(entry, InjuryEntry)
        assert entry.candidate_stats == candidate_stats
        assert entry.primary_dice == primary_dice
        assert entry.primary_fixed == primary_fixed
        assert entry.secondary_amount == secondary_amount


# --- T005: non-injury outcomes ---


def test_mishap_roll_2_is_honorable_discharge_no_debt() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    before = dict(characteristics)
    rolls = ScriptedRolls(d6={RollName.MISHAP: 2})
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert outcome.roll == 2
    assert outcome.discharge_type == "honorable"
    assert outcome.imprisoned is False
    assert outcome.injury_reductions == {}
    assert outcome.injury_crisis is False
    assert debt == 0
    assert result.characteristics == before


def test_mishap_roll_3_is_honorable_discharge_with_legal_debt() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    before = dict(characteristics)
    rolls = ScriptedRolls(d6={RollName.MISHAP: 3})
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert outcome.roll == 3
    assert outcome.discharge_type == "honorable"
    assert outcome.imprisoned is False
    assert outcome.injury_reductions == {}
    assert outcome.injury_crisis is False
    assert debt == 10_000
    assert result.characteristics == before


def test_mishap_roll_4_is_dishonorable_discharge_not_imprisoned() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(d6={RollName.MISHAP: 4})
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert outcome.roll == 4
    assert outcome.discharge_type == "dishonorable"
    assert outcome.imprisoned is False
    assert debt == 0


def test_mishap_roll_5_is_dishonorable_discharge_imprisoned() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(d6={RollName.MISHAP: 5})
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert outcome.roll == 5
    assert outcome.discharge_type == "dishonorable"
    assert outcome.imprisoned is True
    assert debt == 0


# --- T005: injury outcomes (single injury roll, mishap roll 6) ---


def test_mishap_roll_6_injury_row_2_reduces_one_physical_stat_only() -> None:
    # MISHAP=6 (medical, one injury roll); INJURY=2 -> row 2 (all three physical
    # stats are candidates, primary_dice=1, secondary_amount=0); INJURY_STAT picks
    # index 0 -> Strength; INJURY_AMOUNT=3.
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={RollName.MISHAP: 6, RollName.INJURY: 2, RollName.INJURY_AMOUNT: 3},
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert outcome.roll == 6
    assert outcome.discharge_type == "medical"
    assert outcome.injury_reductions == {"Strength": 3}
    assert result.characteristics["Strength"] == 5
    assert result.characteristics["Dexterity"] == 8
    assert result.characteristics["Endurance"] == 8
    assert outcome.injury_crisis is False
    assert debt == 0


def test_mishap_roll_6_injury_row_1_reduces_secondary_stats_by_2() -> None:
    # INJURY=1 -> row 1 (all three physical stats are candidates, primary_dice=1,
    # secondary_amount=2); INJURY_STAT picks index 0 -> Strength; INJURY_AMOUNT=3,
    # so Dexterity and Endurance are the secondaries and each lose 2.
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={RollName.MISHAP: 6, RollName.INJURY: 1, RollName.INJURY_AMOUNT: 3},
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome = result.outcome
    assert outcome.injury_reductions == {"Strength": 3, "Dexterity": 2, "Endurance": 2}
    assert result.characteristics["Strength"] == 5
    assert result.characteristics["Dexterity"] == 6
    assert result.characteristics["Endurance"] == 6


def test_mishap_roll_6_injury_row_3_candidate_pick_excludes_endurance() -> None:
    # INJURY=3 -> row 3 (candidates are Strength/Dexterity only, primary_fixed=2,
    # so no INJURY_AMOUNT roll); INJURY_STAT picks index 1 of that two-item list ->
    # Dexterity. Endurance can never be picked here: it is not a candidate.
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={RollName.MISHAP: 6, RollName.INJURY: 3},
        choices={RollName.INJURY_STAT: 1},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome = result.outcome
    assert outcome.injury_reductions == {"Dexterity": 2}
    assert result.characteristics["Dexterity"] == 6
    assert result.characteristics["Strength"] == 8
    assert result.characteristics["Endurance"] == 8


# --- T006(a): roll twice, take the lower (more severe) result ---


def test_mishap_roll_1_applies_lower_of_two_injury_rolls() -> None:
    # MISHAP=1 -> two INJURY rolls: 5 then 2, so the lower (2) applies, not row 5.
    # INJURY_STAT picks index 0 -> Strength; INJURY_AMOUNT=4.
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={RollName.MISHAP: 1, RollName.INJURY: [5, 2], RollName.INJURY_AMOUNT: 4},
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome = result.outcome
    assert outcome.roll == 1
    assert outcome.discharge_type == "none"
    assert outcome.injury_reductions == {"Strength": 4}
    assert result.characteristics["Strength"] == 4
    assert result.characteristics["Dexterity"] == 8
    assert result.characteristics["Endurance"] == 8


# --- T006(b): injury crisis charges debt and restores the stat to 1 ---


def test_injury_crisis_restores_zeroed_stat_to_one_and_charges_debt() -> None:
    # INJURY=2 -> row 2 (primary_dice=1, secondary_amount=0); INJURY_STAT picks
    # index 0 -> Strength; INJURY_AMOUNT=6 drives Strength 2 - 6 to 0 -> crisis;
    # INJURY_DEBT=3 -> Cr30,000.
    characteristics = {"Strength": 2, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={
            RollName.MISHAP: 6,
            RollName.INJURY: 2,
            RollName.INJURY_AMOUNT: 6,
            RollName.INJURY_DEBT: 3,
        },
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert result.characteristics["Strength"] == 1
    assert outcome.injury_crisis is True
    assert debt == 30_000


# --- T006(c): a single mishap zeroing two stats charges only one crisis debt ---


def test_injury_crisis_zeroing_two_stats_charges_only_one_debt() -> None:
    # INJURY=1 -> row 1 (primary_dice=1, secondary_amount=2); INJURY_STAT picks
    # index 0 -> Strength, so Dexterity/Endurance are the secondaries and both are
    # already low enough to be zeroed by the -2. INJURY_DEBT=1 -> Cr10,000, charged
    # once and not twice.
    characteristics = {"Strength": 8, "Dexterity": 1, "Endurance": 1}
    rolls = ScriptedRolls(
        d6={
            RollName.MISHAP: 6,
            RollName.INJURY: 1,
            RollName.INJURY_AMOUNT: 3,
            RollName.INJURY_DEBT: 1,
        },
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert result.characteristics["Dexterity"] == 1
    assert result.characteristics["Endurance"] == 1
    assert outcome.injury_crisis is True
    assert debt == 10_000


# --- Regression: a stat already at 0 before this mishap's injury (e.g. from prior
# aging) must not spuriously trigger a crisis or get "restored" ---


def test_injury_on_already_zero_stat_does_not_trigger_crisis() -> None:
    # Strength is already 0 (e.g. from prior _apply_aging) before this mishap's
    # injury. INJURY=2 -> row 2 (primary_dice=1, secondary_amount=0); INJURY_STAT
    # picks index 0 -> Strength; INJURY_AMOUNT=3 leaves Strength at 0 (this injury
    # did not drive it there), so no crisis fires and the stat is left as-is.
    characteristics = {"Strength": 0, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={RollName.MISHAP: 6, RollName.INJURY: 2, RollName.INJURY_AMOUNT: 3},
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    outcome, debt = result.outcome, result.debt
    assert outcome.injury_reductions == {"Strength": 3}
    assert result.characteristics["Strength"] == 0
    assert outcome.injury_crisis is False
    assert debt == 0


# --- T006(d): mutates characteristics in place ---


def test_resolve_survival_mishap_returns_the_injured_character_without_mutating() -> None:
    # This test used to assert the opposite: that the caller's dict was mutated in
    # place. Every other step of the engine returns what changed, and this one now
    # does too—the injury comes back on the result and the argument is untouched.
    # MISHAP=6 -> INJURY=2 -> Strength (INJURY_STAT index 0) loses INJURY_AMOUNT=3.
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    rolls = ScriptedRolls(
        d6={RollName.MISHAP: 6, RollName.INJURY: 2, RollName.INJURY_AMOUNT: 3},
        choices={RollName.INJURY_STAT: 0},
    )
    result = resolve_survival_mishap(rolls, characteristics)
    assert result.characteristics["Strength"] == 5
    assert characteristics == {"Strength": 8, "Dexterity": 8, "Endurance": 8}


# --- T007: SC-004 statistical distribution ---


def test_mishap_roll_distribution_within_ten_percent_of_uniform() -> None:
    rolls = RandomRolls()
    results = []
    for _ in range(10_000):
        characteristics = {"Strength": 10, "Dexterity": 10, "Endurance": 10}
        results.append(resolve_survival_mishap(rolls, characteristics))
    counts = Counter(mishap.outcome.roll for mishap in results)
    for roll in range(1, 7):
        assert 1500 <= counts[roll] <= 1834, f"roll {roll} count {counts[roll]} out of tolerance"


# --- Career military classification (guards against silent drift) ---


def test_exactly_the_expected_careers_are_military() -> None:
    from cetools.engine.careers.registry import CAREERS, is_military

    expected_military = {
        "Aerospace System Defense",
        "Marine",
        "Maritime System Defense",
        "Navy",
        "Scout",
        "Surface System Defense",
    }
    actual_military = {career.name for career in CAREERS if is_military(career)}
    assert actual_military == expected_military


def test_military_names_report_draft_keys_missing_from_registry() -> None:
    # DRAFT_TABLE now holds Career objects rather than string keys, so a draft entry
    # naming a career the registry does not know is unrepresentable. The invariant
    # the old key-lookup error guarded is now checked directly: every draftable
    # (hence military) career is a career the registry ships.
    from cetools.engine.careers.registry import CAREERS, DRAFT_TABLE

    assert set(DRAFT_TABLE) <= set(CAREERS)
