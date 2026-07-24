import dataclasses

import pytest

from cetools.engine.ships.tables import (
    ARMOR,
    BRIDGE_SIZES,
    COCKPITS,
    COMPUTERS,
    CONFIG_MODIFIERS,
    DRIVE_COSTS,
    DRIVE_PERFORMANCE,
    ELECTRONICS,
    FITTINGS,
    HULLS,
    QUARTERS,
    SMALL_CRAFT_DRIVE_PERFORMANCE,
    SMALL_CRAFT_ENERGY_CAPS,
    SMALL_CRAFT_HULLS,
    SOFTWARE,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
    ArmorRow,
    CockpitRow,
    ComputerRow,
    DriveRow,
    ElectronicsRow,
    FittingRow,
    HullRow,
    MountRow,
    QuartersRow,
    SoftwareRow,
    WeaponRow,
)

# --- HULLS ---


def test_hulls_keys_match_research_part_b_exactly():
    assert set(HULLS) == {
        100,
        200,
        300,
        400,
        500,
        600,
        700,
        800,
        900,
        1000,
        1200,
        1400,
        1600,
        1800,
        2000,
        3000,
        4000,
        5000,
    }


def test_hulls_keys_are_monotonically_ordered():
    tons = list(HULLS)
    assert tons == sorted(tons)


def test_hulls_codes_are_unique():
    codes = [row.code for row in HULLS.values()]
    assert len(codes) == len(set(codes))


def test_hulls_smallest_and_largest_rows():
    assert HULLS[100] == HullRow(code="1", cost=2, build_weeks=36)
    assert HULLS[5000] == HullRow(code="P", cost=500, build_weeks=428)


# --- Drive costs and performance ---


def test_every_drive_costs_code_is_present_in_drive_performance():
    assert set(DRIVE_COSTS) == set(DRIVE_PERFORMANCE)


def test_drive_codes_skip_i_and_o():
    assert "I" not in DRIVE_COSTS
    assert "O" not in DRIVE_COSTS


def test_drive_codes_run_a_to_z_skipping_i_and_o():
    expected = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    assert set(DRIVE_COSTS) == set(expected)
    assert len(DRIVE_COSTS) == len(expected)


def test_drive_performance_matrix_cells_are_ints():
    for ratings in DRIVE_PERFORMANCE.values():
        for hull_tons, rating in ratings.items():
            assert isinstance(hull_tons, int)
            assert isinstance(rating, int)


def test_drive_performance_hull_tons_are_a_subset_of_hulls():
    all_hulls = set(HULLS)
    for ratings in DRIVE_PERFORMANCE.values():
        assert set(ratings) <= all_hulls


def test_drive_a_is_the_cheapest_smallest_drive():
    assert DRIVE_COSTS["A"] == DriveRow(
        jump_tons=10,
        jump_cost=10,
        maneuver_tons=2,
        maneuver_cost=4,
        power_tons=4,
        power_cost=8,
    )


def test_drive_z_matches_the_srd_top_row():
    assert DRIVE_COSTS["Z"] == DriveRow(
        jump_tons=125,
        jump_cost=240,
        maneuver_tons=47,
        maneuver_cost=96,
        power_tons=73,
        power_cost=192,
    )


def test_drive_performance_a_on_100_tons_is_jump_2():
    assert DRIVE_PERFORMANCE["A"][100] == 2


def test_drive_performance_missing_cell_means_not_installable():
    assert 5000 not in DRIVE_PERFORMANCE["A"]


def test_drive_performance_z_on_5000_tons_is_2():
    assert DRIVE_PERFORMANCE["Z"][5000] == 2


# --- Configuration / armor ---


def test_config_modifiers_match_srd():
    assert CONFIG_MODIFIERS == {"distributed": 0.9, "standard": 1.0, "streamlined": 1.1}


def test_armor_rows_match_srd():
    assert ARMOR["titanium_steel"] == ArmorRow(
        protection_per_5_percent=2, cost_percent_per_5_percent=5, min_tl=7
    )
    assert ARMOR["crystaliron"] == ArmorRow(
        protection_per_5_percent=4, cost_percent_per_5_percent=20, min_tl=10
    )
    assert ARMOR["bonded_superdense"] == ArmorRow(
        protection_per_5_percent=6, cost_percent_per_5_percent=50, min_tl=14
    )


# --- Bridge ---


def test_bridge_steps_are_ordered_by_max_tons_with_none_last():
    max_tons = [step[0] for step in BRIDGE_SIZES]
    assert max_tons[-1] is None
    finite = max_tons[:-1]
    assert finite == sorted(finite)
    assert all(isinstance(t, int) for t in finite)


def test_bridge_sizes_match_srd_steps():
    assert BRIDGE_SIZES == ((200, 10), (1000, 20), (2000, 40), (None, 60))


# --- Computers / software / electronics / quarters ---


def test_computers_cover_models_one_through_seven():
    assert set(COMPUTERS) == {1, 2, 3, 4, 5, 6, 7}


def test_computer_model_one_matches_srd():
    assert COMPUTERS[1] == ComputerRow(tl=7, rating=5, cost=0.03)


def test_computer_model_seven_matches_srd():
    assert COMPUTERS[7] == ComputerRow(tl=15, rating=35, cost=30)


def test_software_fire_control_matches_srd():
    assert SOFTWARE["fire_control"] == SoftwareRow(rating_per_level=5, cost_per_level=2)


def test_software_jump_control_matches_srd():
    assert SOFTWARE["jump_control"] == SoftwareRow(rating_per_level=5, cost_per_level=0.1)


def test_electronics_standard_is_included_in_bridge():
    assert ELECTRONICS["standard"] == ElectronicsRow(tons=0, cost=0)


def test_electronics_very_advanced_matches_srd():
    assert ELECTRONICS["very_advanced"] == ElectronicsRow(tons=5, cost=4)


def test_quarters_stateroom_matches_srd():
    assert QUARTERS["stateroom"] == QuartersRow(tons=4, cost=0.5)


def test_quarters_low_berth_matches_srd():
    assert QUARTERS["low_berth"] == QuartersRow(tons=0.5, cost=0.05)


# --- Fittings ---


def test_fuel_scoops_is_forbidden_on_distributed_hulls():
    assert FITTINGS["fuel_scoops"].forbidden_on_distributed is True


def test_vault_grants_a_hull_structure_bonus():
    assert FITTINGS["vault"].hull_structure_bonus == 4


def test_vehicle_hangar_tonnage_and_cost_are_computed_not_fixed():
    assert FITTINGS["vehicle_hangar"].tons is None
    assert FITTINGS["vehicle_hangar"].cost is None


def test_ordinary_fittings_have_fixed_tons_and_cost():
    for name, row in FITTINGS.items():
        if name == "vehicle_hangar":
            continue
        assert row.tons is not None
        assert row.cost is not None


# --- Turrets ---


def test_turret_mounts_cover_all_five_srd_mount_types():
    assert set(TURRET_MOUNTS) == {"single", "double", "triple", "pop_up", "fixed"}


def test_single_double_triple_turret_costs_match_srd():
    assert TURRET_MOUNTS["single"] == MountRow(tons=1, cost=0.2, weapon_slots=1)
    assert TURRET_MOUNTS["double"] == MountRow(tons=1, cost=0.5, weapon_slots=2)
    assert TURRET_MOUNTS["triple"] == MountRow(tons=1, cost=1, weapon_slots=3)


def test_turret_weapons_cover_the_four_priced_srd_weapons():
    assert set(TURRET_WEAPONS) == {"missile_rack", "pulse_laser", "sandcaster", "particle_beam"}


def test_energy_weapons_are_flagged_for_the_small_craft_cap():
    assert TURRET_WEAPONS["pulse_laser"].energy is True
    assert TURRET_WEAPONS["particle_beam"].energy is True
    assert TURRET_WEAPONS["missile_rack"].energy is False
    assert TURRET_WEAPONS["sandcaster"].energy is False


# --- Small craft (US3) ---


def test_small_craft_hulls_cover_10_to_95_tons_in_5_ton_steps():
    assert set(SMALL_CRAFT_HULLS) == set(range(10, 100, 5))


def test_small_craft_hulls_codes_run_s1_to_sj():
    assert SMALL_CRAFT_HULLS[10] == HullRow(code="s1", cost=1.1, build_weeks=28)
    assert SMALL_CRAFT_HULLS[50] == HullRow(code="s9", cost=1.5, build_weeks=32)
    assert SMALL_CRAFT_HULLS[95] == HullRow(code="sJ", cost=1.95, build_weeks=35)


def test_small_craft_hulls_codes_are_unique():
    codes = [row.code for row in SMALL_CRAFT_HULLS.values()]
    assert len(codes) == len(set(codes))


def test_small_craft_hulls_keys_are_monotonically_ordered():
    tons = list(SMALL_CRAFT_HULLS)
    assert tons == sorted(tons)


def test_cockpits_hold_exactly_the_two_srd_cockpits():
    assert set(COCKPITS) == {"1_man", "2_man"}
    assert COCKPITS["1_man"] == CockpitRow(tons=1.5)
    assert COCKPITS["2_man"] == CockpitRow(tons=3.0)


def test_small_craft_energy_caps_bands_are_exhaustive_over_power_plant_codes():
    assert set(SMALL_CRAFT_ENERGY_CAPS) == set(DRIVE_COSTS)


def test_small_craft_energy_caps_match_srd_bands():
    for code in "ABCDEF":
        assert SMALL_CRAFT_ENERGY_CAPS[code] == 0
    for code in "GHJK":
        assert SMALL_CRAFT_ENERGY_CAPS[code] == 1
    for code in "LMNPQR":
        assert SMALL_CRAFT_ENERGY_CAPS[code] == 2
    for code in "STUVWXYZ":
        assert SMALL_CRAFT_ENERGY_CAPS[code] == 3


def test_small_craft_drive_performance_keys_are_a_subset_of_drive_costs():
    assert set(SMALL_CRAFT_DRIVE_PERFORMANCE) <= set(DRIVE_COSTS)


def test_small_craft_drive_performance_hull_tons_are_a_subset_of_small_craft_hulls():
    all_hulls = set(SMALL_CRAFT_HULLS)
    for ratings in SMALL_CRAFT_DRIVE_PERFORMANCE.values():
        assert set(ratings) <= all_hulls


def test_small_craft_drive_performance_a_on_10_tons_is_2():
    assert SMALL_CRAFT_DRIVE_PERFORMANCE["A"][10] == 2


def test_small_craft_drive_performance_w_on_95_tons_is_6():
    assert SMALL_CRAFT_DRIVE_PERFORMANCE["W"][95] == 6


def test_small_craft_drive_performance_missing_cell_means_not_installable():
    assert 95 not in SMALL_CRAFT_DRIVE_PERFORMANCE["A"]


# --- Every row dataclass field is typed ---


ROW_TYPES = (
    HullRow,
    DriveRow,
    ArmorRow,
    ComputerRow,
    SoftwareRow,
    ElectronicsRow,
    QuartersRow,
    FittingRow,
    MountRow,
    WeaponRow,
    CockpitRow,
)


@pytest.mark.parametrize("row_type", ROW_TYPES, ids=[t.__name__ for t in ROW_TYPES])
def test_every_row_dataclass_field_is_typed(row_type):
    assert dataclasses.is_dataclass(row_type)
    for field in dataclasses.fields(row_type):
        assert field.type not in (None, "")
