import pytest

from cetools.engine.ships import (
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    FittingFit,
    ScreenFit,
    ShipDesign,
    SoftwareFit,
    TurretFit,
    build_ship,
    load_design,
)

_EXAMPLES = "specs/010-starship-generator/examples"


def _small_craft(**overrides):
    kwargs = dict(hull_tons=40, maneuver_code="sB", power_code="sG", bridge=False, cockpit="1_man")
    kwargs.update(overrides)
    return ShipDesign(**kwargs)


# --- SC-002: golden SRD reference designs ---


def test_free_trader_golden_figures():
    ship = build_ship(load_design(f"{_EXAMPLES}/free-trader.toml"))

    assert ship.jump_rating == 1
    assert ship.maneuver_rating == 1
    assert ship.power_rating == 1
    assert ship.assumed_jump_distance == 1
    assert ship.jump_fuel == pytest.approx(20.0)
    assert ship.power_fuel == pytest.approx(2.0)
    assert ship.tonnage_used == pytest.approx(65.0)
    assert ship.cargo_tons == pytest.approx(135.0)
    assert ship.hull_points == 4
    assert ship.structure_points == 4
    assert ship.hardpoints == 2
    assert ship.hardpoints_used == 0
    assert ship.total_cost == pytest.approx(29.772)
    assert ship.build_weeks == 44

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 1
    assert crew.gunners == 0
    assert crew.screen_operators == 0
    assert crew.medic == 1
    assert crew.stewards == 1
    assert crew.total == 5


def test_scout_courier_golden_figures():
    ship = build_ship(load_design(f"{_EXAMPLES}/scout-courier.toml"))

    assert ship.jump_rating == 2
    assert ship.maneuver_rating == 2
    assert ship.power_rating == 2
    assert ship.assumed_jump_distance == 2
    assert ship.jump_fuel == pytest.approx(20.0)
    assert ship.power_fuel == pytest.approx(2.0)
    assert ship.tonnage_used == pytest.approx(62.0)
    assert ship.cargo_tons == pytest.approx(38.0)
    assert ship.hull_points == 2
    assert ship.structure_points == 2
    assert ship.hardpoints == 1
    assert ship.hardpoints_used == 1
    assert ship.total_cost == pytest.approx(28.06)
    assert ship.build_weeks == 36

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 0  # Jump-Control software present
    assert crew.engineers == 1
    assert crew.gunners == 1
    assert crew.screen_operators == 0
    assert crew.medic == 0
    assert crew.stewards == 0
    assert crew.total == 3


def test_fighter_golden_figures():
    ship = build_ship(load_design(f"{_EXAMPLES}/fighter.toml"))

    assert ship.jump_rating == 0
    assert ship.maneuver_rating == 1
    assert ship.power_rating == 3
    assert ship.jump_fuel == pytest.approx(0.0)
    assert ship.power_fuel == pytest.approx(7.3)
    assert ship.tonnage_used == pytest.approx(34.8)
    assert ship.cargo_tons == pytest.approx(5.2)
    assert ship.hull_points == 0
    assert ship.structure_points == 1
    assert ship.hardpoints == 1
    assert ship.hardpoints_used == 1
    assert ship.total_cost == pytest.approx(66.2)
    assert ship.build_weeks == 31

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 1
    assert crew.gunners == 1
    assert crew.screen_operators == 0
    assert crew.medic == 0
    assert crew.stewards == 0
    assert crew.total == 4


def test_heavy_cruiser_golden_figures():
    ship = build_ship(load_design(f"{_EXAMPLES}/heavy-cruiser.toml"))

    assert ship.jump_rating == 1
    assert ship.maneuver_rating == 1
    assert ship.power_rating == 1
    assert ship.assumed_jump_distance == 1
    assert ship.jump_fuel == pytest.approx(100.0)
    assert ship.power_fuel == pytest.approx(10.0)
    assert ship.tonnage_used == pytest.approx(302.0)
    assert ship.cargo_tons == pytest.approx(698.0)
    assert ship.hull_points == 20
    assert ship.structure_points == 20
    assert ship.hardpoints == 10
    assert ship.hardpoints_used == 1
    assert ship.total_cost == pytest.approx(297.16)
    assert ship.build_weeks == 108

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 2
    assert crew.gunners == 1
    assert crew.screen_operators == 1
    assert crew.medic == 0
    assert crew.stewards == 0
    assert crew.total == 6


def test_warship_golden_figures():
    ship = build_ship(load_design(f"{_EXAMPLES}/warship.toml"))

    assert ship.jump_rating == 1
    assert ship.maneuver_rating == 1
    assert ship.power_rating == 1
    assert ship.assumed_jump_distance == 1
    assert ship.jump_fuel == pytest.approx(80.0)
    assert ship.power_fuel == pytest.approx(8.0)
    assert ship.tonnage_used == pytest.approx(264.0)
    assert ship.cargo_tons == pytest.approx(536.0)
    assert ship.hull_points == 16
    assert ship.structure_points == 16
    assert ship.hardpoints == 8
    assert ship.hardpoints_used == 2
    assert ship.total_cost == pytest.approx(183.825)
    assert ship.build_weeks == 92

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 2
    assert crew.gunners == 2
    assert crew.screen_operators == 0
    assert crew.medic == 0
    assert crew.stewards == 0
    assert crew.total == 6


# --- FR-015 / SC-005: rejections, one per builder-enforced constraint ---


def test_rejects_an_untabulated_hull_size():
    design = ShipDesign(hull_tons=150, jump_code="A", power_code="A")
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        build_ship(design)


def test_rejects_a_drive_code_not_available_on_this_hull():
    design = ShipDesign(hull_tons=200, jump_code="Z", power_code="A")
    with pytest.raises(ValueError, match="not available on"):
        build_ship(design)


def test_rejects_a_starship_missing_a_jump_drive():
    design = ShipDesign(hull_tons=200, power_code="A")
    with pytest.raises(ValueError, match="starship requires a jump drive"):
        build_ship(design)


def test_rejects_a_powered_craft_missing_a_power_plant():
    design = ShipDesign(hull_tons=200, jump_code="A")
    with pytest.raises(ValueError, match="powered craft requires a power plant"):
        build_ship(design)


def test_rejects_a_power_plant_below_the_higher_drive_rating():
    design = ShipDesign(hull_tons=200, jump_code="C", power_code="A")
    with pytest.raises(ValueError, match=r"power plant rating 1 below required 3"):
        build_ship(design)


def test_rejects_software_over_the_computer_rating():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        computer=ComputerFit(model=1, software=(SoftwareFit(name="fire_control", level=2),)),
    )
    with pytest.raises(ValueError, match="software rating 10 exceeds computer rating 5"):
        build_ship(design)


def test_rejects_fuel_scoops_on_a_distributed_hull():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        configuration=Configuration.DISTRIBUTED,
        fittings=(FittingFit(kind="fuel_scoops"),),
    )
    with pytest.raises(ValueError, match="a distributed hull cannot mount fuel scoops"):
        build_ship(design)


def test_rejects_more_weapon_systems_than_hardpoints():
    design = ShipDesign(
        hull_tons=100,
        jump_code="A",
        power_code="A",
        turrets=(
            TurretFit(mount="single", weapons=("sandcaster",)),
            TurretFit(mount="single", weapons=("sandcaster",)),
        ),
    )
    with pytest.raises(ValueError, match=r"2 weapon systems exceed 1 hardpoints"):
        build_ship(design)


def test_rejects_tonnage_over_allocation():
    design = ShipDesign(hull_tons=100, jump_code="A", power_code="A", staterooms=30)
    with pytest.raises(ValueError, match="components use .* tons, hull holds 100"):
        build_ship(design)


def test_fuel_scoops_are_allowed_on_a_non_distributed_hull():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        fittings=(FittingFit(kind="fuel_scoops"),),
    )
    build_ship(design)  # does not raise


# --- FR-015: first violation in SRD build order wins ---


def test_first_violation_in_build_order_is_reported():
    # The maneuver-drive step (build order 3) precedes the jump/power steps
    # (4-6); a design broken in both places must report the maneuver error.
    design = ShipDesign(hull_tons=200, maneuver_code="Z", jump_code="A")
    with pytest.raises(ValueError, match="drive code Z is not available"):
        build_ship(design)


def test_hull_size_violation_precedes_a_drive_violation():
    design = ShipDesign(hull_tons=150, jump_code="Z", power_code="A")
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        build_ship(design)


# --- computer hardware option cost combinations ---


def test_computer_jump_control_and_hardened_together_cost_double():
    plain = build_ship(
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", computer=ComputerFit(model=1))
    )
    both = build_ship(
        ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            computer=ComputerFit(model=1, jump_control=True, hardened=True),
        )
    )
    plain_computer_cost = next(
        item.cost for item in plain.line_items if item.name.startswith("computer")
    )
    both_computer_cost = next(
        item.cost for item in both.line_items if item.name.startswith("computer")
    )
    assert both_computer_cost == pytest.approx(plain_computer_cost * 2.0)


def test_computer_single_option_costs_one_and_a_half_times():
    plain = build_ship(
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", computer=ComputerFit(model=1))
    )
    hardened = build_ship(
        ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            computer=ComputerFit(model=1, hardened=True),
        )
    )
    plain_computer_cost = next(
        item.cost for item in plain.line_items if item.name.startswith("computer")
    )
    hardened_computer_cost = next(
        item.cost for item in hardened.line_items if item.name.startswith("computer")
    )
    assert hardened_computer_cost == pytest.approx(plain_computer_cost * 1.5)


def test_armor_options_add_a_per_ton_cost():
    bare = build_ship(
        ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),),
        )
    )
    with_reflec = build_ship(
        ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5, options=("reflec",)),),
        )
    )
    assert with_reflec.total_cost > bare.total_cost


# --- US3: small craft (research.md Part K) ---


def test_small_craft_has_a_cockpit_line_not_a_bridge():
    ship = build_ship(_small_craft())
    assert any(item.name == "1_man cockpit" for item in ship.line_items)
    assert not any(item.name == "bridge" for item in ship.line_items)


def test_small_craft_power_fuel_is_a_one_week_floor_rounded_to_0_1_ton():
    ship = build_ship(_small_craft())
    assert ship.power_fuel == pytest.approx(7.3)


def test_small_craft_has_exactly_one_hardpoint():
    ship = build_ship(_small_craft())
    assert ship.hardpoints == 1


def test_small_craft_jump_rating_is_zero():
    ship = build_ship(_small_craft())
    assert ship.jump_rating == 0
    assert ship.jump_fuel == pytest.approx(0.0)


def test_rejects_a_small_craft_with_a_jump_drive():
    design = _small_craft(jump_code="sB")
    with pytest.raises(ValueError, match="small craft cannot mount a jump drive"):
        build_ship(design)


def test_rejects_energy_weapon_count_over_the_power_plant_cap():
    # sA's band (sA-sF) allows zero energy weapons.
    design = ShipDesign(
        hull_tons=10,
        power_code="sA",
        bridge=False,
        cockpit="1_man",
        turrets=(TurretFit(mount="fixed", weapons=("pulse_laser",)),),
    )
    with pytest.raises(ValueError, match="power plant code sA allows at most 0 energy weapons"):
        build_ship(design)


def test_allows_energy_weapon_count_at_the_power_plant_cap():
    design = _small_craft(turrets=(TurretFit(mount="fixed", weapons=("pulse_laser",)),))
    build_ship(design)  # does not raise: sG's band (sG-sK) allows one


def test_non_energy_weapons_are_never_capped_on_small_craft():
    design = ShipDesign(
        hull_tons=10,
        power_code="sA",
        bridge=False,
        cockpit="1_man",
        turrets=(TurretFit(mount="fixed", weapons=("sandcaster",)),),
    )
    build_ship(design)  # does not raise: sandcaster is not an energy weapon


# --- US4: bays and screens (research.md Part H) ---


def test_bay_consumes_50_tons_plus_1_ton_fire_control_and_one_hardpoint():
    design = ShipDesign(
        hull_tons=1000,
        jump_code="E",
        maneuver_code="E",
        power_code="E",
        bays=(BayFit(kind="particle"),),
    )
    ship = build_ship(design)
    bay_item = next(item for item in ship.line_items if item.name == "particle bay")
    fire_control_item = next(
        item for item in ship.line_items if item.name == "particle bay fire control"
    )
    assert bay_item.tons == pytest.approx(50.0)
    assert bay_item.cost == pytest.approx(20.0)
    assert fire_control_item.tons == pytest.approx(1.0)
    assert ship.hardpoints_used == 1


def test_screen_consumes_50_tons_and_costs_its_srd_price():
    design = ShipDesign(
        hull_tons=1000,
        jump_code="E",
        maneuver_code="E",
        power_code="E",
        screens=(ScreenFit(kind="meson_screen"),),
    )
    ship = build_ship(design)
    screen_item = next(item for item in ship.line_items if item.name == "meson_screen screen")
    assert screen_item.tons == pytest.approx(50.0)
    assert screen_item.cost == pytest.approx(60.0)
    assert ship.hardpoints_used == 0


def test_bay_is_counted_in_crew_gunners_and_screen_in_screen_operators():
    ship = build_ship(load_design(f"{_EXAMPLES}/heavy-cruiser.toml"))
    assert ship.crew.gunners == 1
    assert ship.crew.screen_operators == 1


def test_bay_rejected_when_hardpoints_are_exhausted():
    design = ShipDesign(
        hull_tons=100,
        jump_code="A",
        power_code="A",
        turrets=(TurretFit(mount="single", weapons=("sandcaster",)),),
        bays=(BayFit(kind="particle"),),
    )
    with pytest.raises(ValueError, match=r"2 weapon systems exceed 1 hardpoints"):
        build_ship(design)


def test_bay_rejected_when_free_tonnage_is_under_50():
    # 30 staterooms leave 34 tons free (< the bay's 50t + 1t fire control), but
    # the design is otherwise legal, so the bay alone tips it over.
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        staterooms=30,
        bays=(BayFit(kind="particle"),),
    )
    with pytest.raises(ValueError, match="components use .* tons, hull holds 200"):
        build_ship(design)


def test_bay_on_a_small_craft_is_rejected():
    design = _small_craft(bays=(BayFit(kind="particle"),))
    with pytest.raises(ValueError, match="small craft cannot mount a weapon bay"):
        build_ship(design)
