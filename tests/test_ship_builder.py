import dataclasses
import json
import random
from enum import Enum

import pytest

from cetools.engine.ships import (
    AmmoFit,
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
    render_description,
)
from cetools.engine.ships.tables import (
    AMMO,
    ARMOR,
    ARMOR_OPTIONS,
    BAYS,
    COMPUTERS,
    ELECTRONICS,
    FITTINGS,
    SCREENS,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
    AmmoRow,
    FittingRow,
    ScreenRow,
    WeaponRow,
)

_EXAMPLES = "tests/data/ships"


def _small_craft(**overrides):
    kwargs = dict(hull_tons=40, maneuver_code="sB", power_code="sG", bridge=False, cockpit="1_man")
    kwargs.update(overrides)
    return ShipDesign(**kwargs)


# --- golden SRD reference designs ---


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
    """The Swift Wind is streamlined and declares fuel scoops, so its cost fell
    by the MCr1 it used to be charged for scoops its streamlining already
    includes. The hand-worked reference figures carried that double charge; the
    tonnage is unchanged, because scoops displace nothing either way."""
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
    assert ship.total_cost == pytest.approx(27.06)
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
    assert ship.tonnage_used == pytest.approx(33.8)
    assert ship.cargo_tons == pytest.approx(6.2)
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
    assert ship.tonnage_used == pytest.approx(268.0)
    assert ship.cargo_tons == pytest.approx(532.0)
    assert ship.hull_points == 16
    assert ship.structure_points == 16
    assert ship.armor_protection == 4
    assert ship.hardpoints == 8
    assert ship.hardpoints_used == 3
    assert ship.total_cost == pytest.approx(184.72)
    assert ship.build_weeks == 92

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 2
    assert crew.gunners == 3
    assert crew.screen_operators == 0
    assert crew.medic == 0
    assert crew.stewards == 0
    assert crew.total == 7


def test_warship_loaded_ammunition_is_allocated_and_never_discounted():
    # The fixture's ammunition rides a standard_design hull, so it
    # also pins the rule that the 10% discount never touches ammunition.
    ship = build_ship(load_design(f"{_EXAMPLES}/warship.toml"))

    sand = next(item for item in ship.line_items if item.name == "sand_barrels ammo")
    assert sand.tons == pytest.approx(1.0)
    assert sand.cost == pytest.approx(0.01)
    assert sand.discountable is False

    missiles = next(item for item in ship.line_items if item.name == "standard missile ammo")
    assert missiles.tons == pytest.approx(2.0)
    assert missiles.cost == pytest.approx(0.03)
    assert missiles.discountable is False


# --- rejections, one per builder-enforced constraint ---


def test_rejects_an_untabulated_hull_size():
    design = ShipDesign(hull_tons=150, jump_code="A", power_code="A")
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        build_ship(design)


def test_rejects_a_non_5_percent_armor_increment():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=7),),
    )
    with pytest.raises(ValueError, match="armor must be added in 5% increments"):
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


def test_rejects_power_weeks_below_the_starship_minimum():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", power_weeks=1)
    with pytest.raises(ValueError, match="power_weeks must be >= 2 for a starship"):
        build_ship(design)


def test_rejects_power_weeks_below_the_small_craft_minimum():
    design = _small_craft(power_weeks=0)
    with pytest.raises(ValueError, match="power_weeks must be >= 1 for a small_craft"):
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


def _scooped(configuration, **kwargs):
    """A 200-ton hull of `configuration`, with and without fuel scoops."""
    base = dict(hull_tons=200, jump_code="A", power_code="A", configuration=configuration)
    base.update(kwargs)
    bare = ShipDesign(**base)
    scooped = ShipDesign(**base, fittings=(FittingFit(kind="fuel_scoops"),))
    return build_ship(bare), build_ship(scooped)


def test_a_streamlined_hull_is_not_charged_for_the_scoops_its_streamlining_includes():
    """Compared against the same hull without the entry rather than against a
    literal, so the assertion survives any change to how the x1.1 surcharge is
    computed. Streamlining "includes fuel scoops" (SRD "Ship Configuration")."""
    bare, scooped = _scooped(Configuration.STREAMLINED)

    assert scooped.total_cost == pytest.approx(bare.total_cost)
    assert not any(item.name == "fuel_scoops" for item in scooped.line_items)


def test_a_standard_hull_still_pays_for_its_fuel_scoops():
    """The case that was already right stays right: an unstreamlined ship has to
    buy scoops, and the SRD prices them at MCr1."""
    bare, scooped = _scooped(Configuration.STANDARD)

    assert scooped.total_cost == pytest.approx(bare.total_cost + 1.0)
    assert any(item.name == "fuel_scoops" for item in scooped.line_items)


def test_a_streamlined_hull_keeps_the_redundant_scoops_in_its_design():
    """The charge is dropped, not the entry. A design file round-trips through
    `build_ship` unaltered, so a referee's redundant declaration survives being
    loaded and written back."""
    _, scooped = _scooped(Configuration.STREAMLINED)

    assert [fit.kind for fit in scooped.design.fittings] == ["fuel_scoops"]


def test_redundant_scoops_do_not_change_a_streamlined_hulls_tonnage():
    """Scoops displace nothing, so this holds either way—asserted so that a
    future scoops tonnage cannot quietly go missing along with the charge."""
    bare, scooped = _scooped(Configuration.STREAMLINED)

    assert scooped.tonnage_used == pytest.approx(bare.tonnage_used)
    assert scooped.cargo_tons == pytest.approx(bare.cargo_tons)


# --- Edge case: "Zero remaining tonnage ... is valid" ---


def test_a_design_that_exactly_fills_the_hull_yields_zero_cargo():
    # 10 jump + 4 power + 10 bridge + 20 jump fuel + 2 power fuel + 52 staterooms
    # + 2 low berths = exactly 100 tons. Zero cargo is valid, not an error.
    design = ShipDesign(hull_tons=100, jump_code="A", power_code="A", staterooms=13, low_berths=4)
    ship = build_ship(design)

    assert ship.tonnage_used == pytest.approx(100.0)
    assert ship.cargo_tons == pytest.approx(0.0)


def test_one_half_ton_past_an_exact_fill_is_rejected():
    # The other side of the same boundary: `cargo_tons < 0` is the rejection.
    design = ShipDesign(hull_tons=100, jump_code="A", power_code="A", staterooms=13, low_berths=5)
    with pytest.raises(ValueError, match="components use 100.5 tons, hull holds 100"):
        build_ship(design)


# --- every quarters type the SRD tabulates ---


def test_low_berths_allocate_their_srd_tonnage_and_cost():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", low_berths=4)
    ship = build_ship(design)

    berths = next(item for item in ship.line_items if item.name == "low_berth")
    assert berths.tons == pytest.approx(2.0)  # 0.5 t each
    assert berths.cost == pytest.approx(0.2)  # Cr50,000 each


def test_emergency_low_berths_allocate_their_srd_tonnage_and_cost():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", emergency_low_berths=2)
    ship = build_ship(design)

    berths = next(item for item in ship.line_items if item.name == "emergency_low_berth")
    assert berths.tons == pytest.approx(2.0)  # 1 t each
    assert berths.cost == pytest.approx(0.2)  # Cr100,000 each


def test_all_three_quarters_types_are_allocated_together():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        staterooms=2,
        low_berths=4,
        emergency_low_berths=2,
    )
    ship = build_ship(design)

    quarters = {
        item.name: item.tons
        for item in ship.line_items
        if item.name in ("stateroom", "low_berth", "emergency_low_berth")
    }
    assert quarters == {
        "stateroom": pytest.approx(8.0),
        "low_berth": pytest.approx(2.0),
        "emergency_low_berth": pytest.approx(2.0),
    }


# --- the vault's +4 hull and structure points ---


def _hull_and_structure(**overrides):
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", **overrides)
    ship = build_ship(design)
    return ship.hull_points, ship.structure_points


def test_a_vault_adds_4_hull_and_structure_points():
    bare = _hull_and_structure()
    vaulted = _hull_and_structure(fittings=(FittingFit(kind="vault"),))

    assert bare == (4, 4)
    assert vaulted == (8, 8)


def test_the_vault_bonus_multiplies_by_quantity():
    assert _hull_and_structure(fittings=(FittingFit(kind="vault", quantity=2),)) == (12, 12)


def test_a_vault_allocates_its_srd_tonnage_and_cost():
    design = ShipDesign(
        hull_tons=200, jump_code="A", power_code="A", fittings=(FittingFit(kind="vault"),)
    )
    ship = build_ship(design)

    vault = next(item for item in ship.line_items if item.name == "vault")
    assert vault.tons == pytest.approx(12.0)
    assert vault.cost == pytest.approx(6.0)


def test_a_fitting_without_a_bonus_leaves_hull_and_structure_points_alone():
    assert _hull_and_structure(fittings=(FittingFit(kind="armory"),)) == (4, 4)


def test_a_small_craft_still_carries_a_navigator():
    # The SRD's navigator minimum has exactly one exception
    # (Jump-Control software) and the small-craft section never touches crew, so
    # a jump-incapable small craft still shows a navigator. Inventing a
    # small-craft carve-out the source page does not state would be incorrect.
    ship = build_ship(load_design(f"{_EXAMPLES}/fighter.toml"))

    assert ship.jump_rating == 0
    assert ship.crew.navigator == 1


def test_a_small_craft_navigator_still_yields_to_jump_control_software():
    ship = build_ship(
        _small_craft(computer=ComputerFit(model=2, software=(SoftwareFit("jump_control", 1),)))
    )

    assert ship.crew.navigator == 0


def test_vehicle_hangar_is_sized_and_costed_from_its_vehicle_tons():
    # The vehicle hangar is the one fitting whose figures come
    # from the design (vehicle tons x1.3 tons, MCr0.2/ton) rather than a fixed
    # table row, via FittingRow's per-vehicle-ton columns.
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        fittings=(FittingFit(kind="vehicle_hangar", vehicle_tons=13),),
    )
    ship = build_ship(design)

    hangar = next(item for item in ship.line_items if item.name == "vehicle_hangar")
    assert hangar.tons == pytest.approx(16.9)
    assert hangar.cost == pytest.approx(2.6)


def test_vehicle_hangar_quantity_multiplies_tonnage_and_cost():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        fittings=(FittingFit(kind="vehicle_hangar", quantity=2, vehicle_tons=10),),
    )
    ship = build_ship(design)

    hangar = next(item for item in ship.line_items if item.name == "vehicle_hangar")
    assert hangar.tons == pytest.approx(26.0)
    assert hangar.cost == pytest.approx(4.0)


def test_a_new_vehicle_sized_fitting_needs_no_builder_change(monkeypatch):
    # The builder branches on FittingRow's per-vehicle-ton columns,
    # not on the literal key "vehicle_hangar", so a second SRD vehicle-sized
    # fitting is a data-only edit.
    monkeypatch.setitem(
        FITTINGS,
        "synthetic_bay_deck",
        FittingRow(
            name="a synthetic bay",
            plural="synthetic bays",
            tons=None,
            cost=None,
            tons_per_vehicle_ton=2.0,
            cost_per_vehicle_ton=0.5,
        ),
    )
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        fittings=(FittingFit(kind="synthetic_bay_deck", vehicle_tons=6),),
    )
    ship = build_ship(design)

    deck = next(item for item in ship.line_items if item.name == "synthetic_bay_deck")
    assert deck.tons == pytest.approx(12.0)
    assert deck.cost == pytest.approx(3.0)


def test_a_new_vehicle_sized_fitting_requires_vehicle_tons(monkeypatch):
    monkeypatch.setitem(
        FITTINGS,
        "synthetic_bay_deck",
        FittingRow(
            name="a synthetic bay",
            plural="synthetic bays",
            tons=None,
            cost=None,
            tons_per_vehicle_ton=2.0,
            cost_per_vehicle_ton=0.5,
        ),
    )
    with pytest.raises(ValueError, match="synthetic_bay_deck requires a positive vehicle_tons"):
        FittingFit(kind="synthetic_bay_deck")


# --- first violation in SRD build order wins ---


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


def test_hull_size_violation_precedes_a_power_weeks_violation():
    # Hull (build order 1) precedes fuel (build order after power); a design
    # broken in both places must report the hull error, not the power_weeks
    # error (this is the same defect fixed for the 5%-armor rule).
    design = ShipDesign(hull_tons=150, jump_code="A", power_code="A", power_weeks=1)
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        build_ship(design)


def test_hull_size_violation_precedes_an_armor_increment_violation():
    # Hull (build order 1) precedes armor (build order 2); a design broken in
    # both places must report the hull error, not the armor error.
    design = ShipDesign(
        hull_tons=150,
        jump_code="A",
        power_code="A",
        armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=7),),
    )
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        build_ship(design)


# --- jump-control's "+5 jump rating" (SRD "Ship Computer Options") ---


def test_jump_control_option_raises_the_effective_software_rating_by_5():
    # Model 1's bare rating is 5; fire_control at level 2 costs rating 10,
    # which exceeds a plain model 1 but fits under jump_control's +5 bonus.
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        computer=ComputerFit(
            model=1, jump_control=True, software=(SoftwareFit(name="fire_control", level=2),)
        ),
    )
    build_ship(design)  # does not raise


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


def test_armor_protection_is_zero_for_an_unarmored_ship():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    ship = build_ship(design)
    assert ship.armor_protection == 0


def test_armor_protection_sums_a_single_layer():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=10),),
    )
    ship = build_ship(design)
    assert ship.armor_protection == 4  # 2 increments x 2 protection/5%


def test_armor_protection_sums_stacked_layers_of_different_types():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        armor=(
            ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),
            ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),
        ),
    )
    ship = build_ship(design)
    assert ship.armor_protection == 6  # 2 (titanium steel) + 4 (crystaliron)


def _armored(*, armor_options=(), percent=5, layers=None, hull_tons=200):
    """A 200-ton hull with armor and, optionally, coatings on it."""
    if layers is None:
        layers = (ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=percent),)
    return build_ship(
        ShipDesign(
            hull_tons=hull_tons,
            jump_code="A",
            power_code="A",
            armor=layers,
            armor_options=armor_options,
        )
    )


def test_armor_options_cost_per_ton_of_hull_not_per_ton_of_armor():
    """The SRD prices all three coatings "per ton of hull". cetools charged them
    against the armor layer's tonnage, which on this ship is 10 tons against a
    200-ton hull: a twentyfold understatement."""
    delta = _armored(armor_options=("reflec",)).total_cost - _armored().total_cost

    assert delta == pytest.approx(ARMOR_OPTIONS["reflec"].cost_per_ton * 200)
    assert delta == pytest.approx(20.0)


def test_armor_option_cost_does_not_depend_on_how_much_armor_is_fitted():
    """The sharpest statement of the same rule: the coating is on the hull, so
    thickening the armor under it must not move its price."""
    thin = (
        _armored(percent=5, armor_options=("reflec",)).total_cost - _armored(percent=5).total_cost
    )
    thick = (
        _armored(percent=20, armor_options=("reflec",)).total_cost
        - _armored(percent=20).total_cost
    )

    assert thin == pytest.approx(thick)


def test_an_armor_option_is_charged_once_however_many_layers_it_coats():
    """Reflec "can only be added once". While options hung off a layer, a
    two-layer ship could carry two copies and be billed for both."""
    layers = (
        ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),
        ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),
    )
    delta = (
        _armored(layers=layers, armor_options=("reflec",)).total_cost
        - _armored(layers=layers).total_cost
    )

    assert delta == pytest.approx(ARMOR_OPTIONS["reflec"].cost_per_ton * 200)


@pytest.mark.parametrize("option", sorted(ARMOR_OPTIONS))
def test_every_armor_option_is_priced_per_ton_of_hull(option):
    """Read from the table rather than restated, so a new SRD coating is priced
    by the same rule with no edit here."""
    delta = _armored(armor_options=(option,)).total_cost - _armored().total_cost

    assert delta == pytest.approx(ARMOR_OPTIONS[option].cost_per_ton * 200)


def test_armor_options_add_no_tonnage():
    """A coating displaces nothing; only its cost is the ship's."""
    assert _armored(armor_options=("reflec", "stealth")).tonnage_used == pytest.approx(
        _armored().tonnage_used
    )


def test_armor_options_require_armor_to_coat():
    """The SRD introduces them as options "added to a ship's armor", so a
    coating with nothing under it is refused. Counter-intuitive beside the
    per-hull-ton pricing, and refused anyway: cetools does not overrule a stated
    rule for being surprising."""
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", armor_options=("reflec",))

    with pytest.raises(ValueError, match="armor options require armor to coat: reflec"):
        build_ship(design)


def test_armor_options_are_their_own_line_items():
    """They belong to no layer, so they are not folded into a layer's cost."""
    ship = _armored(armor_options=("reflec",))

    assert any(item.name == "reflec" for item in ship.line_items)


# --- turret ammunition tonnage, cost, and the discount ---


def test_120_missiles_add_10_tons():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        turrets=(
            TurretFit(
                mount="single",
                weapons=("missile_rack",),
                ammo=(AmmoFit(kind="missile", type="standard", count=120),),
            ),
        ),
    )
    ship = build_ship(design)
    ammo_item = next(item for item in ship.line_items if item.name.endswith("ammo"))
    assert ammo_item.tons == pytest.approx(10.0)
    assert ammo_item.cost == pytest.approx(120 * 1_250 / 1_000_000)


def test_sand_barrels_add_tonnage_and_cost():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        turrets=(
            TurretFit(
                mount="single",
                weapons=("sandcaster",),
                ammo=(AmmoFit(kind="sand_barrels", count=20),),
            ),
        ),
    )
    ship = build_ship(design)
    ammo_item = next(item for item in ship.line_items if item.name.endswith("ammo"))
    assert ammo_item.tons == pytest.approx(1.0)
    assert ammo_item.cost == pytest.approx(10_000 / 1_000_000)


def test_standard_design_discount_leaves_ammunition_untouched():
    def make(standard_design):
        return ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            standard_design=standard_design,
            turrets=(
                TurretFit(
                    mount="single",
                    weapons=("missile_rack",),
                    ammo=(AmmoFit(kind="missile", type="standard", count=120),),
                ),
            ),
        )

    plain = build_ship(make(False))
    discounted = build_ship(make(True))

    plain_ammo_cost = next(item.cost for item in plain.line_items if item.name.endswith("ammo"))
    discounted_ammo_cost = next(
        item.cost for item in discounted.line_items if item.name.endswith("ammo")
    )
    assert discounted_ammo_cost == pytest.approx(plain_ammo_cost)

    non_ammo_plain = plain.total_cost - plain_ammo_cost
    non_ammo_discounted = discounted.total_cost - discounted_ammo_cost
    assert non_ammo_discounted == pytest.approx(non_ammo_plain * 0.9)


def test_a_fitting_whose_name_ends_in_fuel_is_still_discounted(monkeypatch):
    # The discount exemption is `LineItem.discountable`, not a
    # `name.endswith("fuel"/"ammo")` check, so a fitting that happens to be
    # named like fuel is not silently exempted.
    monkeypatch.setitem(
        FITTINGS,
        "backup_fuel",
        FittingRow(name="a backup fuel tank", plural="backup fuel tanks", tons=1, cost=1.0),
    )

    def make(standard_design):
        return ShipDesign(
            hull_tons=200,
            jump_code="A",
            power_code="A",
            standard_design=standard_design,
            fittings=(FittingFit(kind="backup_fuel"),),
        )

    plain = build_ship(make(False))
    discounted = build_ship(make(True))
    assert discounted.total_cost == pytest.approx(plain.total_cost * 0.9)


def test_small_craft_armor_floors_at_1_ton_per_5_percent_rather_than_rejecting():
    # The SRD armor-by-type table's "minimum 1 ton" applies
    # even when 5% of a small hull is under 1 ton (10 t x 5% = 0.5 t); the SRD
    # text makes this a floor, not a rejection.
    design = ShipDesign(
        hull_tons=10,
        power_code="sA",
        bridge=False,
        cockpit="1_man",
        armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),),
    )
    ship = build_ship(design)  # does not raise
    armor_item = next(item for item in ship.line_items if item.name.endswith("armor"))
    assert armor_item.tons == pytest.approx(1.0)


# --- bridge/cockpit must pair with the hull's HullClass ---


def test_rejects_a_small_craft_built_with_a_bridge():
    design = ShipDesign(hull_tons=40, maneuver_code="sB", power_code="sG", bridge=True)
    with pytest.raises(ValueError, match="small craft requires a cockpit, not a bridge"):
        build_ship(design)


def test_rejects_a_starship_built_with_a_cockpit():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        bridge=False,
        cockpit="1_man",
    )
    with pytest.raises(ValueError, match="a starship requires a bridge, not a cockpit"):
        build_ship(design)


# --- small craft (SRD "Small Craft Design") ---


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


# --- bays and screens (SRD "Bays", "Screens") ---


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


# --- the derived tech level ---


def _tl(**overrides):
    """Build a minimal starship with `overrides` and return its tech level."""
    kwargs = dict(hull_tons=200, jump_code="A", power_code="A")
    kwargs.update(overrides)
    return build_ship(ShipDesign(**kwargs)).tech_level


def test_a_design_with_no_purchased_electronics_still_derives_at_least_eight():
    # Every ship carries the Standard package included in its bridge
    # or cockpit, so the derived value has a floor of ELECTRONICS["standard"].tl.
    assert _tl() == ELECTRONICS["standard"].tl == 8


def test_the_small_craft_floor_is_the_same_standard_package():
    assert build_ship(_small_craft()).tech_level == ELECTRONICS["standard"].tl


def test_derived_tech_level_is_the_max_over_fitted_rows():
    # Crystaliron (10) beats the Model 1 computer (7) and Standard sensors (8).
    assert (
        _tl(
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),), computer=ComputerFit(model=1)
        )
        == ARMOR["crystaliron"].tl
        == 10
    )


def test_a_purchased_electronics_package_raises_the_derived_tech_level():
    assert _tl(electronics="very_advanced") == ELECTRONICS["very_advanced"].tl == 12


def test_a_computer_raises_the_derived_tech_level():
    assert _tl(computer=ComputerFit(model=7)) == COMPUTERS[7].tl == 15


def test_an_armor_option_raises_the_derived_tech_level():
    # Stealth is TL 11, above titanium steel's 7 and the Standard floor of 8.
    assert (
        _tl(
            armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),),
            armor_options=("stealth",),
        )
        == ARMOR_OPTIONS["stealth"].tl
        == 11
    )


def test_a_turret_mount_contributes_its_tech_level():
    assert _tl(turrets=(TurretFit(mount="pop_up", weapons=("sandcaster",)),)) == 10
    assert TURRET_MOUNTS["pop_up"].tl == 10


def test_a_turret_weapon_contributes_its_tech_level(monkeypatch):
    # Every tabulated turret weapon is TL 6-8, at or below the Standard-sensor
    # floor, so a synthetic row is what makes the weapon's contribution visible.
    assert max(row.tl for row in TURRET_WEAPONS.values()) <= ELECTRONICS["standard"].tl
    monkeypatch.setitem(
        TURRET_WEAPONS,
        "synthetic_cannon",
        WeaponRow(name="synthetic cannon", plural="synthetic cannons", cost=3.5, tl=16),
    )
    assert _tl(turrets=(TurretFit(mount="single", weapons=("synthetic_cannon",)),)) == 16


def test_ammunition_contributes_its_own_tech_level(monkeypatch):
    assert AMMO["missile_smart"].tl == 8
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
            tl=14,
            weapon="missile_rack",
        ),
    )
    assert (
        _tl(
            turrets=(
                TurretFit(
                    mount="single",
                    weapons=("missile_rack",),
                    ammo=(AmmoFit(kind="missile", type="decoy", count=12),),
                ),
            )
        )
        == 14
    )


def test_a_bay_and_a_screen_contribute_their_tech_levels():
    assert (
        build_ship(load_design(f"{_EXAMPLES}/heavy-cruiser.toml")).tech_level
        >= SCREENS["meson_screen"].tl
    )
    design = ShipDesign(
        hull_tons=1000, jump_code="E", maneuver_code="E", power_code="E", bays=(BayFit("fusion"),)
    )
    assert build_ship(design).tech_level == BAYS["fusion"].tl == 12


def test_a_fixed_mount_contributes_no_tech_level():
    # The SRD prints "-" in the fixed mounting's TL cell.
    assert TURRET_MOUNTS["fixed"].tl is None
    assert _tl(turrets=(TurretFit(mount="fixed", weapons=("missile_rack",)),)) == 8


@pytest.mark.parametrize(
    "overrides",
    [
        {"hull_tons": 800, "jump_code": "D", "maneuver_code": "D", "power_code": "D"},
        {"configuration": Configuration.STREAMLINED},
        {"fittings": (FittingFit(kind="vault"), FittingFit(kind="library"))},
        {"staterooms": 4, "low_berths": 6, "emergency_low_berths": 2},
        {"computer": ComputerFit(model=1, software=(SoftwareFit(name="jump_control", level=1),))},
    ],
    ids=["hull-and-drives", "configuration", "fittings", "quarters", "software"],
)
def test_untabulated_categories_contribute_nothing(overrides):
    # Hulls, drives, configurations, cockpits, quarters,
    # fittings and software carry no SRD tech level. This is a finding, not an
    # omission -- inventing one would not be supported by the SRD.
    assert _tl(**overrides) == ELECTRONICS["standard"].tl


def test_an_explicit_tech_level_above_the_derived_value_is_used_as_given():
    assert _tl(tech_level=15) == 15


def test_an_explicit_tech_level_below_the_derived_value_is_used_as_given():
    # Never clamped, never warned about. A TL 3 hull yard building a
    # TL 12 sensor suite is the designer's statement, not cetools' to correct.
    assert _tl(electronics="very_advanced", tech_level=3) == 3


def test_an_explicit_tech_level_of_zero_is_used_as_given():
    assert _tl(tech_level=0) == 0


def test_the_derived_tech_level_changes_no_other_computed_value():
    # Supplying design.tech_level is presentation only.
    plain = build_ship(ShipDesign(hull_tons=200, jump_code="A", power_code="A"))
    overridden = build_ship(
        ShipDesign(hull_tons=200, jump_code="A", power_code="A", tech_level=15)
    )
    assert overridden.tech_level == 15
    assert plain.tech_level == 8
    assert dataclasses.replace(plain, design=overridden.design, tech_level=15) == overridden


# --- build_ship never assigns a name --------------------------------------


def test_build_ship_assigns_no_name():
    design = ShipDesign(hull_tons=100, jump_code="A", power_code="A", name=None)
    ship = build_ship(design)

    assert ship.design.name is None
    assert "Unnamed Ship" in render_description(ship)


def test_build_ship_consumes_no_randomness(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("build_ship must not consume randomness")

    monkeypatch.setattr(random.Random, "random", _boom)
    design = ShipDesign(hull_tons=100, jump_code="A", power_code="A")

    build_ship(design)  # does not raise


# --- authored designs are unaffected by fuel-limited fitting ---

_AUTHORED_DESIGNS_PATH = "tests/data/baseline/authored_designs.json"
_AUTHORED_EXAMPLES = (
    "tests/data/ships/fighter.toml",
    "tests/data/ships/free-trader.toml",
    "tests/data/ships/heavy-cruiser.toml",
    "tests/data/ships/scout-courier.toml",
    "tests/data/ships/warship.toml",
    "tests/data/ships/subsidized-merchant.toml",
)


def test_fr012_an_authored_short_legged_design_builds_exactly_as_written():
    # A design specifying a jump_distance below one full jump at its drive's
    # rating must build unaltered, never silently corrected up to the rating.
    design = ShipDesign(hull_tons=200, jump_code="C", power_code="C", jump_distance=1)
    ship = build_ship(design)

    assert ship.jump_rating == 3
    assert ship.assumed_jump_distance == 1
    assert ship.jump_fuel == pytest.approx(20.0)


def _to_jsonable(value):
    if dataclasses.is_dataclass(value):
        return {f.name: _to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


@pytest.mark.parametrize("path", _AUTHORED_EXAMPLES)
def test_sc010_authored_example_designs_build_unchanged_from_before_the_change(path):
    with open(_AUTHORED_DESIGNS_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)

    ship = build_ship(load_design(path))
    assert _to_jsonable(ship) == baseline[path]


def test_a_new_row_with_a_tech_level_widens_the_derivation_with_no_code_change(monkeypatch):
    # The walk is over the fitted components' rows, not over a
    # per-category list of "things that have a TL".
    monkeypatch.setitem(
        SCREENS,
        "synthetic_screen",
        ScreenRow(name="synthetic screen", plural="synthetic screens", tons=50, cost=42.0, tl=17),
    )
    design = ShipDesign(
        hull_tons=1000,
        jump_code="E",
        maneuver_code="E",
        power_code="E",
        screens=(ScreenFit(kind="synthetic_screen"),),
    )
    assert build_ship(design).tech_level == 17
