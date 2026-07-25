import dataclasses

import pytest

from cetools.engine.ships.models import (
    AmmoFit,
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    Crew,
    FittingFit,
    HullClass,
    LineItem,
    ScreenFit,
    Ship,
    ShipDesign,
    SoftwareFit,
    TurretFit,
)

# --- Enums ---


def test_configuration_members_and_cost_modifiers():
    assert Configuration.DISTRIBUTED.cost_modifier == 0.9
    assert Configuration.STANDARD.cost_modifier == 1.0
    assert Configuration.STREAMLINED.cost_modifier == 1.1


def test_armor_type_members():
    assert {m.value for m in ArmorType} == {"titanium_steel", "crystaliron", "bonded_superdense"}


def test_hull_class_members():
    assert {m.value for m in HullClass} == {"starship", "small_craft"}


# --- ArmorFit ---


def test_armor_fit_accepts_a_valid_layer():
    fit = ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=10, options=("reflec",))
    assert fit.percent == 10


def test_armor_fit_accepts_a_non_5_percent_increment_shape_only():
    # The 5% rule is an SRD rule, not a shape constraint (FR-015): only
    # `build_ship`'s armor step rejects it, so construction here succeeds.
    fit = ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=7)
    assert fit.percent == 7


def test_armor_fit_rejects_zero_percent():
    with pytest.raises(ValueError, match="must be positive"):
        ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=0)


def test_armor_fit_rejects_an_unknown_option():
    with pytest.raises(ValueError, match="unknown armor option"):
        ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5, options=("laser_resistant",))


def test_armor_fit_rejects_a_repeated_option():
    with pytest.raises(ValueError, match="not repeat"):
        ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5, options=("reflec", "reflec"))


# --- SoftwareFit / ComputerFit ---


def test_software_fit_accepts_a_known_program():
    assert SoftwareFit(name="fire_control", level=2).level == 2


def test_software_fit_rejects_an_unknown_name():
    with pytest.raises(ValueError, match="unknown software"):
        SoftwareFit(name="autopilot", level=1)


def test_software_fit_rejects_a_non_positive_level():
    with pytest.raises(ValueError, match="positive"):
        SoftwareFit(name="fire_control", level=0)


def test_computer_fit_accepts_a_valid_model():
    fit = ComputerFit(model=3, jump_control=True)
    assert fit.model == 3


def test_computer_fit_rejects_an_unknown_model():
    with pytest.raises(ValueError, match="unknown computer model"):
        ComputerFit(model=8)


# --- FittingFit ---


def test_fitting_fit_accepts_a_known_kind():
    assert FittingFit(kind="armory", quantity=2).quantity == 2


def test_fitting_fit_rejects_an_unknown_kind():
    with pytest.raises(ValueError, match="unknown fitting"):
        FittingFit(kind="holodeck")


def test_fitting_fit_rejects_a_non_positive_quantity():
    with pytest.raises(ValueError, match="quantity must be positive"):
        FittingFit(kind="armory", quantity=0)


def test_vehicle_hangar_requires_vehicle_tons():
    with pytest.raises(ValueError, match="vehicle_hangar requires"):
        FittingFit(kind="vehicle_hangar")


def test_vehicle_hangar_accepts_vehicle_tons():
    assert FittingFit(kind="vehicle_hangar", vehicle_tons=13).vehicle_tons == 13


def test_vehicle_tons_rejected_on_a_non_hangar_fitting():
    with pytest.raises(ValueError, match="only meaningful for vehicle_hangar"):
        FittingFit(kind="armory", vehicle_tons=13)


# --- AmmoFit / TurretFit ---


def test_ammo_fit_accepts_sand_barrels():
    assert AmmoFit(kind="sand_barrels", count=20).count == 20


def test_ammo_fit_accepts_missile_with_a_type():
    assert AmmoFit(kind="missile", count=12, type="standard").type == "standard"


def test_ammo_fit_rejects_an_unknown_kind():
    with pytest.raises(ValueError, match="unknown ammo kind"):
        AmmoFit(kind="torpedoes", count=1)


def test_ammo_fit_rejects_missile_without_a_type():
    with pytest.raises(ValueError, match="unknown missile type"):
        AmmoFit(kind="missile", count=12)


def test_ammo_fit_rejects_type_on_sand_barrels():
    with pytest.raises(ValueError, match="only meaningful for missile"):
        AmmoFit(kind="sand_barrels", count=20, type="standard")


def test_ammo_fit_rejects_non_positive_count():
    with pytest.raises(ValueError, match="count must be positive"):
        AmmoFit(kind="sand_barrels", count=0)


def test_turret_fit_accepts_a_valid_double_turret():
    fit = TurretFit(mount="double", weapons=("pulse_laser", "sandcaster"))
    assert fit.weapons == ("pulse_laser", "sandcaster")


def test_turret_fit_rejects_an_unknown_mount():
    with pytest.raises(ValueError, match="unknown turret mount"):
        TurretFit(mount="quad", weapons=("pulse_laser",))


def test_turret_fit_rejects_an_unknown_weapon():
    with pytest.raises(ValueError, match="unknown turret weapon"):
        TurretFit(mount="single", weapons=("death_ray",))


def test_turret_fit_rejects_more_weapons_than_slots():
    with pytest.raises(ValueError, match="holds at most 1"):
        TurretFit(mount="single", weapons=("pulse_laser", "sandcaster"))


def test_turret_fit_rejects_no_weapons():
    with pytest.raises(ValueError, match="at least one weapon"):
        TurretFit(mount="single", weapons=())


# --- BayFit / ScreenFit ---


def test_bay_fit_accepts_a_known_kind():
    assert BayFit(kind="particle").kind == "particle"


def test_bay_fit_rejects_an_unknown_kind():
    with pytest.raises(ValueError, match="unknown bay kind"):
        BayFit(kind="railgun")


def test_screen_fit_accepts_a_known_kind():
    assert ScreenFit(kind="meson_screen").kind == "meson_screen"


def test_screen_fit_rejects_an_unknown_kind():
    with pytest.raises(ValueError, match="unknown screen kind"):
        ScreenFit(kind="deflector")


# --- ShipDesign: shape-only validation ---


def test_ship_design_derives_starship_hull_class():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    assert design.hull_class == HullClass.STARSHIP
    assert design.power_weeks == 2


def test_ship_design_derives_small_craft_hull_class():
    design = ShipDesign(hull_tons=50, bridge=False, cockpit="1_man", power_code="sA")
    assert design.hull_class == HullClass.SMALL_CRAFT
    assert design.power_weeks == 1


def test_ship_design_rejects_non_positive_hull_tons():
    with pytest.raises(ValueError, match="hull_tons"):
        ShipDesign(hull_tons=0)


def test_ship_design_rejects_a_drive_code_outside_the_srd_sequence():
    with pytest.raises(ValueError, match="jump_code"):
        ShipDesign(hull_tons=200, jump_code="I", power_code="A")


def test_ship_design_rejects_a_negative_jump_distance():
    with pytest.raises(ValueError, match="jump_distance"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", jump_distance=-1)


def test_ship_design_accepts_power_weeks_below_the_starship_minimum_shape_only():
    # The >= 2 (starship) / >= 1 (small craft) floor is an SRD rule, not a shape
    # constraint (FR-015): only `build_ship`'s fuel step rejects it, so
    # construction here succeeds.
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", power_weeks=1)
    assert design.power_weeks == 1


def test_ship_design_accepts_power_weeks_below_the_small_craft_minimum_shape_only():
    design = ShipDesign(
        hull_tons=50, bridge=False, cockpit="1_man", power_code="sA", power_weeks=0
    )
    assert design.power_weeks == 0


def test_ship_design_rejects_bridge_and_cockpit_both_set():
    with pytest.raises(ValueError, match="exactly one of bridge or cockpit"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", bridge=True, cockpit="1_man")


def test_ship_design_rejects_neither_bridge_nor_cockpit():
    with pytest.raises(ValueError, match="exactly one of bridge or cockpit"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", bridge=False)


def test_ship_design_rejects_an_unknown_electronics_package():
    with pytest.raises(ValueError, match="electronics"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", electronics="quantum_radar")


@pytest.mark.parametrize(
    "field",
    ["staterooms", "low_berths", "emergency_low_berths", "passengers_high", "passengers_middle"],
)
def test_ship_design_rejects_negative_counts(field):
    with pytest.raises(ValueError, match=field):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", **{field: -1})


def test_shape_only_validation_allows_a_rules_illegal_but_well_formed_design():
    # A small craft carrying a jump drive is SRD-illegal, but it is a
    # structurally well-formed ShipDesign: shape validation must not reject it,
    # so build_ship (Phase 3) is the sole authority that does (FR-015).
    design = ShipDesign(
        hull_tons=50,
        bridge=False,
        cockpit="1_man",
        jump_code="A",
        power_code="sA",
    )
    assert design.jump_code == "A"
    assert design.hull_class == HullClass.SMALL_CRAFT


# --- Crew ---


def test_crew_total_includes_every_role():
    crew = Crew(
        pilot=1,
        navigator=1,
        engineers=2,
        gunners=3,
        screen_operators=1,
        medic=1,
        stewards=2,
    )
    assert crew.total == 11


def test_crew_total_with_no_screen_operators():
    crew = Crew(
        pilot=1, navigator=0, engineers=1, gunners=0, screen_operators=0, medic=0, stewards=0
    )
    assert crew.total == 2


def test_crew_rejects_a_negative_role_count():
    with pytest.raises(ValueError, match="gunners"):
        Crew(
            pilot=1, navigator=1, engineers=0, gunners=-1, screen_operators=0, medic=0, stewards=0
        )


# --- LineItem ---


def test_line_item_fields():
    item = LineItem(name="Hull", tons=200, cost=8)
    assert item.name == "Hull"
    assert item.tons == 200
    assert item.cost == 8


def test_line_item_rejects_negative_tons():
    with pytest.raises(ValueError, match="tons"):
        LineItem(name="Hull", tons=-1, cost=0)


def test_line_item_rejects_negative_cost():
    with pytest.raises(ValueError, match="cost"):
        LineItem(name="Hull", tons=0, cost=-1)


# --- Frozen / immutable behaviour ---


@pytest.mark.parametrize(
    "instance",
    [
        ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),
        ComputerFit(model=1),
        FittingFit(kind="armory"),
        TurretFit(mount="single", weapons=("pulse_laser",)),
        BayFit(kind="particle"),
        ScreenFit(kind="meson_screen"),
        ShipDesign(hull_tons=200, jump_code="A", power_code="A"),
        Crew(
            pilot=1, navigator=1, engineers=0, gunners=0, screen_operators=0, medic=0, stewards=0
        ),
        LineItem(name="Hull", tons=200, cost=8),
    ],
)
def test_instances_are_frozen(instance):
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.name = "mutated"  # type: ignore[attr-defined]


def test_ship_is_frozen():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    crew = Crew(
        pilot=1, navigator=1, engineers=0, gunners=0, screen_operators=0, medic=0, stewards=0
    )
    ship = Ship(
        design=design,
        tech_level=8,
        hull_tons=200,
        configuration=Configuration.STANDARD,
        jump_rating=1,
        maneuver_rating=1,
        power_rating=1,
        jump_fuel=20,
        assumed_jump_distance=1,
        power_fuel=2,
        tonnage_used=100,
        cargo_tons=100,
        hull_points=4,
        structure_points=4,
        armor_protection=0,
        hardpoints=2,
        hardpoints_used=0,
        crew=crew,
        total_cost=8,
        build_weeks=44,
        line_items=(),
    )
    assert ship.cargo_tons == 100
    with pytest.raises(dataclasses.FrozenInstanceError):
        ship.cargo_tons = 0  # type: ignore[misc]


def test_ship_rejects_negative_cargo_tons():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    crew = Crew(
        pilot=1, navigator=1, engineers=0, gunners=0, screen_operators=0, medic=0, stewards=0
    )
    with pytest.raises(ValueError, match="cargo_tons"):
        Ship(
            design=design,
            tech_level=8,
            hull_tons=200,
            configuration=Configuration.STANDARD,
            jump_rating=1,
            maneuver_rating=1,
            power_rating=1,
            jump_fuel=20,
            assumed_jump_distance=1,
            power_fuel=2,
            tonnage_used=250,
            cargo_tons=-50,
            hull_points=4,
            structure_points=4,
            armor_protection=0,
            hardpoints=2,
            hardpoints_used=0,
            crew=crew,
            total_cost=8,
            build_weeks=44,
            line_items=(),
        )


# --- USDF: ShipDesign.purpose / ShipDesign.tech_level / Ship.tech_level ---


def _ship(**overrides):
    """A minimal well-formed `Ship`, for validation tests only."""
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    crew = Crew(
        pilot=1, navigator=1, engineers=0, gunners=0, screen_operators=0, medic=0, stewards=0
    )
    kwargs = dict(
        design=design,
        tech_level=8,
        hull_tons=200,
        configuration=Configuration.STANDARD,
        jump_rating=1,
        maneuver_rating=1,
        power_rating=1,
        jump_fuel=20,
        assumed_jump_distance=1,
        power_fuel=2,
        tonnage_used=100,
        cargo_tons=100,
        hull_points=4,
        structure_points=4,
        armor_protection=0,
        hardpoints=2,
        hardpoints_used=0,
        crew=crew,
        total_cost=8,
        build_weeks=44,
        line_items=(),
    )
    kwargs.update(overrides)
    return Ship(**kwargs)


def test_ship_design_purpose_and_tech_level_default_to_none():
    # Every existing design file stays valid and every existing design stays
    # buildable (spec Assumptions).
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    assert design.purpose is None
    assert design.tech_level is None


def test_ship_design_accepts_an_authored_purpose_and_tech_level():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        purpose="a subsidized merchant plying the backwaters",
        tech_level=12,
    )
    assert design.purpose == "a subsidized merchant plying the backwaters"
    assert design.tech_level == 12


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_ship_design_rejects_an_empty_or_whitespace_purpose(bad):
    with pytest.raises(ValueError, match="purpose"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", purpose=bad)


@pytest.mark.parametrize("bad", [1, 2.5, ["a starship"]])
def test_ship_design_rejects_a_non_string_purpose(bad):
    with pytest.raises(ValueError, match="purpose"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", purpose=bad)


def test_ship_design_rejects_a_negative_tech_level():
    with pytest.raises(ValueError, match="tech_level"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", tech_level=-1)


def test_ship_design_accepts_a_tech_level_of_zero():
    assert ShipDesign(hull_tons=200, jump_code="A", power_code="A", tech_level=0).tech_level == 0


@pytest.mark.parametrize("bad", [8.0, "8", True, False])
def test_ship_design_rejects_a_non_integer_tech_level(bad):
    # A bool is an int subclass, so it is rejected explicitly: `tech_level =
    # true` in a TOML file is an authoring error, not tech level 1.
    with pytest.raises(ValueError, match="tech_level"):
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", tech_level=bad)


def test_ship_design_does_not_check_tech_level_against_any_derived_value():
    # FR-028b: an explicit tech level is a statement about the yard that built
    # the ship, not a constraint. A TL far below any fitted component's is
    # accepted as given.
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", tech_level=1)
    assert design.tech_level == 1


def test_ship_carries_a_tech_level():
    assert _ship().tech_level == 8


def test_ship_rejects_a_negative_tech_level():
    with pytest.raises(ValueError, match="tech_level"):
        _ship(tech_level=-1)


def test_ship_accepts_a_tech_level_of_zero():
    assert _ship(tech_level=0).tech_level == 0
