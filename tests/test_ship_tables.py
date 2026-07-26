import dataclasses

import pytest

from cetools.engine.ships import build_ship, load_design
from cetools.engine.ships.models import (
    AmmoFit,
    ArmorFit,
    ArmorType,
    BayFit,
    Configuration,
    Crew,
    FittingFit,
    ScreenFit,
    ShipDesign,
    TurretFit,
)
from cetools.engine.ships.tables import (
    AMMO,
    ARMOR,
    ARMOR_OPTIONS,
    BAYS,
    BRIDGE_SIZES,
    COCKPITS,
    COMPUTERS,
    CONFIGURATIONS,
    CREW_POSITIONS,
    DRIVE_COSTS,
    DRIVE_PERFORMANCE,
    ELECTRONICS,
    FITTINGS,
    HULLS,
    QUARTERS,
    SCREENS,
    SMALL_CRAFT_DRIVE_PERFORMANCE,
    SMALL_CRAFT_ENERGY_CAPS,
    SMALL_CRAFT_HULLS,
    SOFTWARE,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
    AmmoRow,
    ArmorOptionRow,
    ArmorRow,
    BayRow,
    CockpitRow,
    ComputerRow,
    ConfigurationRow,
    CrewPositionRow,
    DriveRow,
    ElectronicsRow,
    FittingRow,
    HullRow,
    MountRow,
    QuartersRow,
    ScreenRow,
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


def test_drive_costs_jump_tons_strictly_increasing_in_table_order():
    # research.md Part C, invariant 1: the fit search relies on this being
    # true rather than assuming it, but a future SRD row that breaks it
    # should fail loudly here rather than silently mis-selecting a drive.
    jump_tons = [row.jump_tons for row in DRIVE_COSTS.values()]
    assert all(a < b for a, b in zip(jump_tons, jump_tons[1:]))


def test_drive_performance_rating_non_decreasing_per_hull_in_table_order():
    # research.md Part C, invariant 2.
    letters = list(DRIVE_COSTS)
    for hull_tons in HULLS:
        ratings = [
            DRIVE_PERFORMANCE[letter][hull_tons]
            for letter in letters
            if hull_tons in DRIVE_PERFORMANCE[letter]
        ]
        assert all(a <= b for a, b in zip(ratings, ratings[1:]))


# --- Configuration / armor ---


def test_configuration_cost_modifiers_match_srd():
    assert {key: row.cost_modifier for key, row in CONFIGURATIONS.items()} == {
        "distributed": 0.9,
        "standard": 1.0,
        "streamlined": 1.1,
    }


def test_armor_rows_match_srd():
    assert ARMOR["titanium_steel"] == ArmorRow(
        name="Titanium Steel", protection_per_5_percent=2, cost_percent_per_5_percent=5, tl=7
    )
    assert ARMOR["crystaliron"] == ArmorRow(
        name="Crystaliron", protection_per_5_percent=4, cost_percent_per_5_percent=20, tl=10
    )
    assert ARMOR["bonded_superdense"] == ArmorRow(
        name="Bonded Superdense", protection_per_5_percent=6, cost_percent_per_5_percent=50, tl=14
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
    assert ELECTRONICS["standard"] == ElectronicsRow(name="Standard", tons=0, cost=0, tl=8, dm=-4)


def test_electronics_very_advanced_matches_srd():
    assert ELECTRONICS["very_advanced"] == ElectronicsRow(
        name="Very Advanced", tons=5, cost=4, tl=12, dm=2
    )


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
    assert TURRET_MOUNTS["single"] == MountRow(
        name="single turret", plural="single turrets", tons=1, cost=0.2, weapon_slots=1, tl=7
    )
    assert TURRET_MOUNTS["double"] == MountRow(
        name="double turret", plural="double turrets", tons=1, cost=0.5, weapon_slots=2, tl=8
    )
    assert TURRET_MOUNTS["triple"] == MountRow(
        name="triple turret", plural="triple turrets", tons=1, cost=1, weapon_slots=3, tl=9
    )


def test_fixed_mounting_occupies_no_tonnage_at_half_a_single_turrets_cost():
    assert TURRET_MOUNTS["fixed"] == MountRow(
        name="fixed mounting",
        plural="fixed mountings",
        tons=0,
        cost=0.1,
        weapon_slots=1,
        tl=None,
    )


def test_turret_weapons_cover_the_four_priced_srd_weapons():
    assert set(TURRET_WEAPONS) == {"missile_rack", "pulse_laser", "sandcaster", "particle_beam"}


def test_energy_weapons_are_flagged_for_the_small_craft_cap():
    assert TURRET_WEAPONS["pulse_laser"].energy is True
    assert TURRET_WEAPONS["particle_beam"].energy is True
    assert TURRET_WEAPONS["missile_rack"].energy is False
    assert TURRET_WEAPONS["sandcaster"].energy is False


# --- Bays / screens (US4, research.md Part H) ---


def test_bays_cover_the_four_srd_kinds_at_50_tons_each():
    assert set(BAYS) == {"missile_bank", "particle", "meson", "fusion"}
    for row in BAYS.values():
        assert row.tons == 50


def test_bays_match_srd_costs():
    assert BAYS["missile_bank"] == BayRow(
        name="missile bay", plural="missile bays", tons=50, cost=12, tl=6
    )
    assert BAYS["particle"] == BayRow(
        name="particle beam bay", plural="particle beam bays", tons=50, cost=20, tl=8
    )
    assert BAYS["meson"] == BayRow(
        name="meson gun bay", plural="meson gun bays", tons=50, cost=50, tl=11
    )
    assert BAYS["fusion"] == BayRow(
        name="fusion gun bay", plural="fusion gun bays", tons=50, cost=8, tl=12
    )


def test_screens_cover_the_two_srd_kinds_at_50_tons_each():
    assert set(SCREENS) == {"meson_screen", "nuclear_damper"}
    for row in SCREENS.values():
        assert row.tons == 50


def test_screens_match_srd_costs():
    assert SCREENS["meson_screen"] == ScreenRow(
        name="meson screen", plural="meson screens", tons=50, cost=60, tl=12
    )
    assert SCREENS["nuclear_damper"] == ScreenRow(
        name="nuclear damper", plural="nuclear dampers", tons=50, cost=50, tl=12
    )


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
    ArmorOptionRow,
    AmmoRow,
    ComputerRow,
    SoftwareRow,
    ElectronicsRow,
    QuartersRow,
    FittingRow,
    MountRow,
    WeaponRow,
    CockpitRow,
    BayRow,
    ScreenRow,
    ConfigurationRow,
    CrewPositionRow,
)


@pytest.mark.parametrize("row_type", ROW_TYPES, ids=[t.__name__ for t in ROW_TYPES])
def test_every_row_dataclass_field_is_typed(row_type):
    assert dataclasses.is_dataclass(row_type)
    for field in dataclasses.fields(row_type):
        assert field.type not in (None, "")


# --- SC-006: a new SRD entry is a data-only edit, no builder/generator change ---


def test_a_new_fitting_row_costs_and_allocates_correctly_with_no_code_change(monkeypatch):
    monkeypatch.setitem(
        FITTINGS,
        "synthetic_gadget",
        FittingRow(name="a synthetic gadget", plural="synthetic gadgets", tons=3, cost=1.25),
    )

    design = load_design("specs/010-starship-generator/examples/free-trader.toml")
    design = dataclasses.replace(
        design,
        fittings=design.fittings + (FittingFit(kind="synthetic_gadget", quantity=2),),
    )

    ship = build_ship(design)

    gadget_items = [item for item in ship.line_items if item.name == "synthetic_gadget"]
    assert len(gadget_items) == 1
    assert gadget_items[0].tons == pytest.approx(6.0)
    assert gadget_items[0].cost == pytest.approx(2.5)
    assert ship.tonnage_used == pytest.approx(65.0 + 6.0)
    assert ship.cargo_tons == pytest.approx(135.0 - 6.0)


def test_a_new_distributed_forbidden_fitting_rejects_on_a_distributed_hull_with_no_code_change(
    monkeypatch,
):
    # T079: builder.py reads `FittingRow.forbidden_on_distributed`, not a
    # hardcoded `fit.kind == "fuel_scoops"` comparison, so a second SRD fitting
    # forbidden on a distributed hull is a data-only edit (SC-006).
    monkeypatch.setitem(
        FITTINGS,
        "synthetic_shield",
        FittingRow(
            name="a synthetic shield",
            plural="synthetic shields",
            tons=1,
            cost=0.1,
            forbidden_on_distributed=True,
        ),
    )
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        configuration=Configuration.DISTRIBUTED,
        fittings=(FittingFit(kind="synthetic_shield"),),
    )
    with pytest.raises(ValueError, match="a distributed hull cannot mount synthetic shield"):
        build_ship(design)


def test_a_new_bay_row_is_accepted_and_allocated_with_no_code_change(monkeypatch):
    # T087: BayFit validates against BAYS itself, not a hardcoded copy of its
    # keys, so a new SRD bay is a data-only edit (SC-006).
    monkeypatch.setitem(
        BAYS,
        "synthetic_bay",
        BayRow(name="synthetic bay", plural="synthetic bays", tons=50, cost=17.5, tl=9),
    )

    design = load_design("specs/010-starship-generator/examples/free-trader.toml")
    design = dataclasses.replace(design, bays=(BayFit(kind="synthetic_bay"),))

    ship = build_ship(design)

    bay_item = next(item for item in ship.line_items if item.name == "synthetic_bay bay")
    assert bay_item.tons == pytest.approx(50.0)
    assert bay_item.cost == pytest.approx(17.5)
    assert ship.hardpoints_used == 1
    assert ship.crew.gunners == 1


def test_a_new_screen_row_is_accepted_and_allocated_with_no_code_change(monkeypatch):
    monkeypatch.setitem(
        SCREENS,
        "synthetic_screen",
        ScreenRow(name="synthetic screen", plural="synthetic screens", tons=50, cost=42.0, tl=9),
    )

    design = load_design("specs/010-starship-generator/examples/free-trader.toml")
    design = dataclasses.replace(design, screens=(ScreenFit(kind="synthetic_screen"),))

    ship = build_ship(design)

    screen_item = next(item for item in ship.line_items if item.name == "synthetic_screen screen")
    assert screen_item.tons == pytest.approx(50.0)
    assert screen_item.cost == pytest.approx(42.0)
    assert ship.crew.screen_operators == 1


def test_a_new_ammo_row_is_accepted_and_costed_with_no_code_change(monkeypatch):
    # The AMMO key is descriptive only: models.py and builder.py both match an
    # AmmoFit on the row's kind/type columns (SC-006).
    monkeypatch.setitem(
        AMMO,
        "missile_decoy",
        AmmoRow(
            name="decoy missile",
            plural="decoy missiles",
            kind="missile",
            type="decoy",
            rounds_per_ton=12,
            cost_per_round=0.002,
            tl=8,
            weapon="missile_rack",
        ),
    )

    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        turrets=(
            TurretFit(
                mount="single",
                weapons=("missile_rack",),
                ammo=(AmmoFit(kind="missile", type="decoy", count=24),),
            ),
        ),
    )
    ship = build_ship(design)

    ammo_item = next(item for item in ship.line_items if item.name == "decoy missile ammo")
    assert ammo_item.tons == pytest.approx(2.0)
    assert ammo_item.cost == pytest.approx(0.048)
    assert ammo_item.discountable is False


def test_a_new_armor_option_row_is_accepted_and_costed_with_no_code_change(monkeypatch):
    # T087: the armor-option surcharge is table data read by builder.py, not a
    # dict living in the builder, so a new SRD option is a data-only edit.
    monkeypatch.setitem(
        ARMOR_OPTIONS,
        "synthetic_coating",
        ArmorOptionRow(name="a synthetic coating", cost_per_ton=0.25, tl=9),
    )

    def armor_cost(options):
        design = ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5, options=options),),
        )
        item = next(i for i in build_ship(design).line_items if i.name == "titanium_steel armor")
        return item.tons, item.cost

    bare_tons, bare_cost = armor_cost(())
    coated_tons, coated_cost = armor_cost(("synthetic_coating",))

    assert bare_tons == pytest.approx(10.0)
    assert coated_tons == pytest.approx(10.0)
    assert coated_cost == pytest.approx(bare_cost + 0.25 * 10.0)


def test_a_new_hull_row_costs_and_allocates_correctly_with_no_code_change(monkeypatch):
    # T091/SC-006: a new hull size is a data edit to HULLS plus the drive
    # performance the SRD tabulates for it -- no builder or generator change.
    monkeypatch.setitem(HULLS, 250, HullRow(code="X", cost=10, build_weeks=50))
    monkeypatch.setitem(DRIVE_PERFORMANCE, "A", {**DRIVE_PERFORMANCE["A"], 250: 1})

    ship = build_ship(ShipDesign(hull_tons=250, jump_code="A", power_code="A"))

    assert ship.build_weeks == 50
    assert ship.hull_points == 5
    assert ship.structure_points == 5
    assert ship.hardpoints == 2
    assert next(i for i in ship.line_items if i.name == "hull").cost == pytest.approx(10.0)
    assert ship.jump_fuel == pytest.approx(25.0)
    assert ship.tonnage_used == pytest.approx(10 + 4 + 20 + 25 + 2)


# --- USDF display names, plurals, tech levels and dice modifiers (data-model.md section 4) ---


NAMEABLE_TABLES = {
    "ARMOR": ARMOR,
    "ARMOR_OPTIONS": ARMOR_OPTIONS,
    "ELECTRONICS": ELECTRONICS,
    "TURRET_MOUNTS": TURRET_MOUNTS,
    "TURRET_WEAPONS": TURRET_WEAPONS,
    "AMMO": AMMO,
    "BAYS": BAYS,
    "SCREENS": SCREENS,
    "FITTINGS": FITTINGS,
}

COUNTABLE_TABLES = {
    "TURRET_MOUNTS": TURRET_MOUNTS,
    "TURRET_WEAPONS": TURRET_WEAPONS,
    "AMMO": AMMO,
    "BAYS": BAYS,
    "SCREENS": SCREENS,
    "FITTINGS": FITTINGS,
}


@pytest.mark.parametrize("table_name", sorted(NAMEABLE_TABLES))
def test_every_nameable_row_carries_a_non_empty_srd_name(table_name):
    # FR-030: the renderer never spells a component; every name it can print
    # lives on the component's own data row.
    for key, row in NAMEABLE_TABLES[table_name].items():
        assert hasattr(row, "name"), f"{table_name}[{key!r}] has no name column"
        assert isinstance(row.name, str)
        assert row.name.strip(), f"{table_name}[{key!r}].name is empty"


@pytest.mark.parametrize("table_name", sorted(COUNTABLE_TABLES))
def test_every_countable_row_carries_a_non_empty_explicit_plural(table_name):
    # research.md Part E: plurals are spelled, never derived by suffix, because
    # the SRD's own are irregular ("armory" -> "armories").
    for key, row in COUNTABLE_TABLES[table_name].items():
        assert hasattr(row, "plural"), f"{table_name}[{key!r}] has no plural column"
        assert isinstance(row.plural, str)
        assert row.plural.strip(), f"{table_name}[{key!r}].plural is empty"


def test_every_ammo_row_names_the_turret_weapon_it_feeds():
    # FR-031: the ammunition sentence names its weapon through data, not
    # through the renderer knowing that missiles go in missile racks.
    for key, row in AMMO.items():
        assert row.weapon in TURRET_WEAPONS, f"AMMO[{key!r}].weapon is not a TURRET_WEAPONS key"


def test_every_electronics_row_carries_a_tech_level_and_a_dice_modifier():
    for key, row in ELECTRONICS.items():
        assert isinstance(row.tl, int), f"ELECTRONICS[{key!r}].tl is not an int"
        assert isinstance(row.dm, int), f"ELECTRONICS[{key!r}].dm is not an int"


def test_electronics_names_tech_levels_and_dms_match_srd():
    assert ELECTRONICS["standard"] == ElectronicsRow(name="Standard", tons=0, cost=0, tl=8, dm=-4)
    assert ELECTRONICS["basic_civilian"] == ElectronicsRow(
        name="Basic Civilian", tons=1, cost=0.05, tl=9, dm=-2
    )
    assert ELECTRONICS["basic_military"] == ElectronicsRow(
        name="Basic Military", tons=2, cost=1, tl=10, dm=0
    )
    assert ELECTRONICS["advanced"] == ElectronicsRow(name="Advanced", tons=3, cost=2, tl=11, dm=1)
    assert ELECTRONICS["very_advanced"] == ElectronicsRow(
        name="Very Advanced", tons=5, cost=4, tl=12, dm=2
    )


def test_only_the_fixed_mounting_has_no_tech_level():
    # research.md Part D: the SRD prints "-" in the fixed mounting's TL cell,
    # and only there.
    for key, row in TURRET_MOUNTS.items():
        if key == "fixed":
            assert row.tl is None
        else:
            assert isinstance(row.tl, int), f"TURRET_MOUNTS[{key!r}].tl is not an int"


def test_armor_rows_carry_tl_and_no_longer_carry_min_tl():
    # ArmorRow.min_tl is renamed tl: it is the SRD's TL column and is now read
    # by the tech-level derivation, no longer a deliberately unenforced column.
    field_names = {f.name for f in dataclasses.fields(ArmorRow)}
    assert "tl" in field_names
    assert "min_tl" not in field_names
    for key, row in ARMOR.items():
        assert isinstance(row.tl, int), f"ARMOR[{key!r}].tl is not an int"


def test_armor_option_names_and_tech_levels_match_srd():
    assert ARMOR_OPTIONS["reflec"] == ArmorOptionRow(
        name="a reflec coating", cost_per_ton=0.1, tl=10
    )
    assert ARMOR_OPTIONS["self_sealing"] == ArmorOptionRow(
        name="a self-sealing hull", cost_per_ton=0.01, tl=9
    )
    assert ARMOR_OPTIONS["stealth"] == ArmorOptionRow(
        name="a stealth coating", cost_per_ton=0.1, tl=11
    )


def test_turret_mount_and_weapon_tech_levels_match_srd():
    assert [TURRET_MOUNTS[k].tl for k in ("single", "double", "triple", "pop_up")] == [7, 8, 9, 10]
    assert TURRET_WEAPONS["missile_rack"].tl == 6
    assert TURRET_WEAPONS["pulse_laser"].tl == 7
    assert TURRET_WEAPONS["sandcaster"].tl == 7
    assert TURRET_WEAPONS["particle_beam"].tl == 8


def test_turret_weapons_are_named_for_the_armament_clause_not_the_catalog():
    # research.md Part E: "armed with missiles", never "armed with missile racks".
    assert (TURRET_WEAPONS["missile_rack"].name, TURRET_WEAPONS["missile_rack"].plural) == (
        "missile",
        "missiles",
    )
    assert (TURRET_WEAPONS["pulse_laser"].name, TURRET_WEAPONS["pulse_laser"].plural) == (
        "pulse laser",
        "pulse lasers",
    )


def test_ammo_names_and_tech_levels_match_srd():
    assert AMMO["sand_barrels"].name == "canister"
    assert AMMO["sand_barrels"].plural == "canisters"
    assert AMMO["sand_barrels"].tl == 5
    assert AMMO["missile_standard"].tl == 6
    assert AMMO["missile_nuclear"].tl == 6
    assert AMMO["missile_smart"].tl == 8
    assert AMMO["missile_smart"].name == "smart missile"
    assert AMMO["missile_smart"].plural == "smart missiles"


def test_bay_and_screen_names_and_tech_levels_match_srd():
    assert (BAYS["missile_bank"].name, BAYS["missile_bank"].tl) == ("missile bay", 6)
    assert (BAYS["particle"].name, BAYS["particle"].tl) == ("particle beam bay", 8)
    assert (BAYS["meson"].name, BAYS["meson"].tl) == ("meson gun bay", 11)
    assert (BAYS["fusion"].name, BAYS["fusion"].tl) == ("fusion gun bay", 12)
    assert (SCREENS["meson_screen"].name, SCREENS["meson_screen"].tl) == ("meson screen", 12)
    assert (SCREENS["nuclear_damper"].name, SCREENS["nuclear_damper"].tl) == ("nuclear damper", 12)


def test_fitting_names_carry_an_article_and_plurals_do_not():
    # research.md Part E: "an armory" / "armories", "fuel scoops" / "fuel scoops".
    assert FITTINGS["armory"].name == "an armory"
    assert FITTINGS["armory"].plural == "armories"
    assert FITTINGS["fuel_scoops"].name == "fuel scoops"
    assert FITTINGS["fuel_scoops"].plural == "fuel scoops"
    assert FITTINGS["vehicle_hangar"].name == "a small craft hangar"
    assert FITTINGS["vehicle_hangar"].plural == "small craft hangars"
    for key, row in FITTINGS.items():
        assert not row.plural.startswith(("a ", "an ")), f"FITTINGS[{key!r}].plural has an article"


def test_only_fuel_processors_and_luxuries_are_counted_in_tons():
    counted = {key for key, row in FITTINGS.items() if row.counted_in_tons}
    assert counted == {"fuel_processor", "luxuries"}


def test_only_the_fuel_processor_states_an_unrefined_fuel_throughput():
    rates = {key: row.unrefined_fuel_per_ton for key, row in FITTINGS.items()}
    assert rates["fuel_processor"] == 20.0
    assert all(rate is None for key, rate in rates.items() if key != "fuel_processor")


def test_fittings_carry_no_tech_level_because_the_srd_tabulates_none():
    # research.md Part D: a finding, not an omission. Adding a column the SRD
    # does not fill would be inventing data.
    field_names = {f.name for f in dataclasses.fields(FittingRow)}
    assert "tl" not in field_names


# --- CONFIGURATIONS and CREW_POSITIONS (data-model.md section 4) ---


def test_configurations_is_keyed_by_every_configuration_value():
    assert set(CONFIGURATIONS) == {member.value for member in Configuration}


def test_configuration_rows_match_srd_with_lower_case_names():
    assert CONFIGURATIONS["distributed"] == ConfigurationRow(name="distributed", cost_modifier=0.9)
    assert CONFIGURATIONS["standard"] == ConfigurationRow(name="standard", cost_modifier=1.0)
    assert CONFIGURATIONS["streamlined"] == ConfigurationRow(name="streamlined", cost_modifier=1.1)


def test_configuration_names_are_lower_case():
    # research.md Part E: the starship examples print "The hull is standard".
    for row in CONFIGURATIONS.values():
        assert row.name == row.name.lower()


def test_config_modifiers_is_gone():
    import cetools.engine.ships.tables as tables_module

    assert not hasattr(tables_module, "CONFIG_MODIFIERS")


def test_every_crew_position_field_names_a_crew_count_attribute():
    crew_fields = {f.name for f in dataclasses.fields(Crew)}
    for row in CREW_POSITIONS:
        assert row.field in crew_fields, f"CREW_POSITIONS field {row.field!r} is not a Crew field"


def test_every_crew_count_attribute_appears_exactly_once():
    crew_fields = [f.name for f in dataclasses.fields(Crew)]
    listed = [row.field for row in CREW_POSITIONS]
    assert sorted(listed) == sorted(crew_fields)
    assert len(listed) == len(set(listed))


def test_crew_positions_are_in_the_fr_018_print_order():
    assert [row.field for row in CREW_POSITIONS] == [
        "pilot",
        "navigator",
        "engineers",
        "gunners",
        "screen_operators",
        "medic",
        "stewards",
    ]


def test_crew_position_names_and_plurals_match_srd():
    assert CREW_POSITIONS[0] == CrewPositionRow(field="pilot", name="pilot", plural="pilots")
    assert CREW_POSITIONS[4] == CrewPositionRow(
        field="screen_operators", name="screen operator", plural="screen operators"
    )
    for row in CREW_POSITIONS:
        assert row.name.strip()
        assert row.plural.strip()


def test_a_new_turret_weapon_row_costs_correctly_with_no_code_change(monkeypatch):
    monkeypatch.setitem(
        TURRET_WEAPONS,
        "synthetic_cannon",
        WeaponRow(name="synthetic cannon", plural="synthetic cannons", cost=3.5, tl=8),
    )

    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        turrets=(TurretFit(mount="single", weapons=("synthetic_cannon",)),),
    )
    ship = build_ship(design)

    turret_item = next(item for item in ship.line_items if item.name == "single turret")
    assert turret_item.tons == pytest.approx(TURRET_MOUNTS["single"].tons)
    assert turret_item.cost == pytest.approx(TURRET_MOUNTS["single"].cost + 3.5)
