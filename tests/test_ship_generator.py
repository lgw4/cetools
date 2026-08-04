import json
import math
import time
from dataclasses import fields

import pytest

from cetools.engine.rolls import RandomRolls, RecordingRolls, RollName, ScriptedRolls
from cetools.engine.ships import (
    ABSENT,
    SHIP_NAMES,
    UNCONSTRAINED,
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    DesignConstraints,
    FittingFit,
    GenerationResult,
    HullClass,
    ScreenFit,
    Ship,
    ShipDesign,
    TurretPin,
    UnmetConstraint,
    build_ship,
    dump_design,
    load_design,
    loads_design,
    validate_electronics,
    validate_hull_tons,
    validate_turret_count,
    validate_turret_mount,
    validate_turret_weapon,
)
from cetools.engine.ships.generator import (
    _ARMOR_CHOICES,
    _FITTING_CHOICES,
    Drive,
    TonnageLedger,
    _energy_allowance,
    _exceeds_energy_allowance,
    armor_options,
    available_ratings,
    bay_kinds,
    computer_models,
    electronics_packages,
    fitting_kinds,
    generate_ship,
    hardpoints,
    hull_tonnages,
    offerable_ratings,
    screen_kinds,
    small_craft_maneuver_ratings,
    small_craft_power_ratings,
    small_craft_weapons,
    turret_mounts,
    turret_weapons,
    validate_small_craft_weapon,
)
from cetools.engine.ships.tables import (
    ARMOR_OPTIONS,
    BAYS,
    COMPUTERS,
    DRIVE_COSTS,
    DRIVE_PERFORMANCE,
    ELECTRONICS,
    FITTINGS,
    HULLS,
    SCREENS,
    SMALL_CRAFT_ENERGY_CAPS,
    SMALL_CRAFT_HULLS,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)

_SMALL_CRAFT = DesignConstraints(hull_class=HullClass.SMALL_CRAFT)
_CATALOG_NAMES = {entry.name for entry in SHIP_NAMES}
_PRE_CHANGE_SWEEP_PATH = "tests/data/baseline/pre_change_sweep.json"
_POST_CHANGE_BASELINE_PATH = "tests/data/baseline/designs.json"

# --- Engine accessors: the published value sets ---


def _names(recorder: RecordingRolls) -> list[RollName]:
    """Every roll name the recorder saw, in order.

    `RecordingRolls` keeps whole `Draw` records; these tests only ever ask which
    names were drawn and in what order, so they flatten to that here.
    """
    return [draw.name for draw in recorder.draws]


def test_accessor_hull_tonnages_starship_matches_validate_hull_tons():
    values = hull_tonnages(HullClass.STARSHIP)
    assert values == tuple(sorted(HULLS))
    for tons in values:
        validate_hull_tons(HullClass.STARSHIP, tons)
    for tons in HULLS:
        assert tons in values


def test_accessor_hull_tonnages_small_craft_matches_validate_hull_tons():
    values = hull_tonnages(HullClass.SMALL_CRAFT)
    assert values == tuple(sorted(SMALL_CRAFT_HULLS))
    for tons in values:
        validate_hull_tons(HullClass.SMALL_CRAFT, tons)
    for tons in SMALL_CRAFT_HULLS:
        assert tons in values


def test_accessor_armor_options_matches_ship_design_validation():
    """Every option the accessor offers is one a design will accept. The
    validation lives on `ShipDesign` rather than on `ArmorFit`, because a coating
    is on the hull."""
    values = armor_options()
    assert values == tuple(ARMOR_OPTIONS)
    for option in values:
        ShipDesign(hull_tons=200, armor_options=(option,))
    for option in ARMOR_OPTIONS:
        assert option in values


def test_accessor_computer_models_matches_computer_fit_validation():
    values = computer_models()
    assert values == tuple(sorted(COMPUTERS))
    for model in values:
        ComputerFit(model=model)
    for model in COMPUTERS:
        assert model in values


def test_accessor_electronics_packages_matches_validate_electronics():
    values = electronics_packages()
    assert values == tuple(ELECTRONICS)
    assert values[0] == "standard"
    for name in values:
        validate_electronics(name)
    for name in ELECTRONICS:
        assert name in values


def test_accessor_bay_kinds_matches_bay_fit_validation():
    values = bay_kinds()
    assert values == tuple(BAYS)
    for kind in values:
        BayFit(kind=kind)
    for kind in BAYS:
        assert kind in values


def test_accessor_screen_kinds_matches_screen_fit_validation():
    values = screen_kinds()
    assert values == tuple(SCREENS)
    for kind in values:
        ScreenFit(kind=kind)
    for kind in SCREENS:
        assert kind in values


def test_accessor_turret_mounts_matches_validate_turret_mount():
    values = turret_mounts()
    assert values == tuple(TURRET_MOUNTS)
    for mount in values:
        validate_turret_mount(mount)
    for mount in TURRET_MOUNTS:
        assert mount in values


def test_accessor_turret_weapons_matches_validate_turret_weapon():
    values = turret_weapons()
    assert values == tuple(TURRET_WEAPONS)
    for weapon in values:
        validate_turret_weapon(weapon)
    for weapon in TURRET_WEAPONS:
        assert weapon in values


def test_accessor_fitting_kinds_omits_vehicle_sized_fittings():
    """The exclusion is derived from the table row, not from a list of names,
    so the expected sequence is spelled the same way—by row shape.
    Naming the excluded keys here would fail the day a second vehicle-sized
    fitting arrived, though the accessor would have dropped it correctly.

    `vehicle_hangar` is still named once, as the anchor for the one instance
    the table has today; that assertion stays true however many more are
    added.
    """
    values = fitting_kinds()
    assert "vehicle_hangar" not in values
    assert values == tuple(kind for kind, row in FITTINGS.items() if row.tons is not None)
    for kind in values:
        FittingFit(kind=kind)
    for kind, row in FITTINGS.items():
        if row.tons is not None:
            assert kind in values
        else:
            assert kind not in values


def test_accessor_fitting_kinds_drops_what_a_streamlined_hull_already_carries():
    """Derived from the row's column rather than from the name `fuel_scoops`, so
    a second SRD component included by streamlining drops out with no edit."""
    narrowed = fitting_kinds(Configuration.STREAMLINED)

    assert "fuel_scoops" not in narrowed
    assert narrowed == tuple(
        kind
        for kind, row in FITTINGS.items()
        if row.tons is not None and not row.included_on_streamlined
    )


def test_accessor_fitting_kinds_drops_what_a_distributed_hull_cannot_mount():
    """Derived from the row's column rather than from the name `fuel_scoops`, so
    a second SRD component forbidden to a shape drops out with no edit."""
    narrowed = fitting_kinds(Configuration.DISTRIBUTED)

    assert "fuel_scoops" not in narrowed
    assert narrowed == tuple(
        kind
        for kind, row in FITTINGS.items()
        if row.tons is not None and not row.forbidden_on_distributed
    )


def test_accessor_fitting_kinds_keeps_scoops_on_a_standard_hull():
    """The shape that neither includes scoops nor forbids them is the one that
    has to buy them, so it is the one still offered them."""
    assert "fuel_scoops" in fitting_kinds(Configuration.STANDARD)


def test_accessor_fitting_kinds_is_unnarrowed_without_a_configuration():
    """What a caller passes while the shape is still to be drawn: nothing can be
    ruled out yet, so nothing is."""
    assert fitting_kinds(None) == fitting_kinds()


@pytest.mark.parametrize("hull_tons, power_rating", [(40, 1), (95, 6), (10, 2)])
def test_accessor_small_craft_weapons_narrows_by_energy_allowance_and_mount(
    hull_tons, power_rating
):
    for mount in (None, *turret_mounts()):
        values = small_craft_weapons(hull_tons, power_rating, mount)
        allowance = _energy_allowance(hull_tons, power_rating)
        expected = tuple(
            weapon
            for weapon in turret_weapons()
            if not _exceeds_energy_allowance(allowance, weapon, mount)
        )
        assert values == expected
        for weapon in values:
            validate_small_craft_weapon(hull_tons, power_rating, weapon, mount)
        for weapon in turret_weapons():
            if weapon not in values:
                with pytest.raises(ValueError):
                    validate_small_craft_weapon(hull_tons, power_rating, weapon, mount)


@pytest.mark.parametrize(
    "hull_class, hull_tons",
    [(HullClass.STARSHIP, 200), (HullClass.STARSHIP, 1000), (HullClass.SMALL_CRAFT, 40)],
)
def test_accessor_hardpoints_pinned_matches_validate_turret_count(hull_class, hull_tons):
    count = hardpoints(hull_class, hull_tons)
    validate_turret_count(hull_class, hull_tons, count)
    with pytest.raises(ValueError):
        validate_turret_count(hull_class, hull_tons, count + 1)


def test_accessor_hardpoints_unpinned_starship_is_ruleset_maximum():
    assert hardpoints(HullClass.STARSHIP, None) == max(HULLS) // 100


def test_accessor_hardpoints_unpinned_small_craft_is_one():
    assert hardpoints(HullClass.SMALL_CRAFT, None) == 1


# --- TonnageLedger: the budget the selection steps spend against ---


def test_ledger_starts_with_the_tonnage_it_was_given():
    assert TonnageLedger(42.5).remaining == pytest.approx(42.5)


def test_ledger_spending_reduces_what_remains():
    ledger = TonnageLedger(100.0)
    ledger.spend(30.0)
    ledger.spend(0.5)
    assert ledger.remaining == pytest.approx(69.5)


def test_ledger_affords_exactly_what_remains():
    """The boundary is inclusive: a component costing every remaining ton fits.

    The threaded-float code this replaced declined only when `tons > remaining`,
    so an exact fit was affordable. Flipping this to exclusive would silently
    drop components that used to be installed.
    """
    ledger = TonnageLedger(10.0)
    assert ledger.affords(10.0)
    assert not ledger.affords(10.1)


def test_ledger_affords_nothing_once_overspent():
    ledger = TonnageLedger(1.0)
    ledger.spend(1.0)
    assert ledger.affords(0.0)
    assert not ledger.affords(0.1)


def test_ledger_records_nothing_until_something_is_declined():
    assert TonnageLedger(100.0).declined == ()


def test_ledger_records_declines_in_order_with_their_reasons():
    ledger = TonnageLedger(5.0)
    ledger.decline("armor", "crystaliron 10%", "none", "needs 20.0t, 5.0t free")
    ledger.decline("bays", "particle", "none", "needs 51.0t, 5.0t free")

    assert [d.field for d in ledger.declined] == ["armor", "bays"]
    assert ledger.declined[0].asked == "crystaliron 10%"
    assert ledger.declined[0].reason == "needs 20.0t, 5.0t free"


def test_ledger_declined_is_a_snapshot_not_a_live_view():
    ledger = TonnageLedger(5.0)
    before = ledger.declined
    ledger.decline("screens", "meson", "none", "needs 50.0t, 5.0t free")
    assert before == ()
    assert len(ledger.declined) == 1


def test_ledger_declining_does_not_move_the_budget():
    """Recording a decline is bookkeeping, not an allocation."""
    ledger = TonnageLedger(5.0)
    ledger.decline("armor", "crystaliron 10%", "none", "needs 20.0t, 5.0t free")
    assert ledger.remaining == pytest.approx(5.0)


# --- GenerationResult: what generation produced, and what it could not honor ---


def test_generate_ship_returns_a_result_carrying_the_ship():
    result = generate_ship(ScriptedRolls())

    assert isinstance(result, GenerationResult)
    assert isinstance(result.ship, Ship)
    assert result.ship.hull_tons == 100


def test_unconstrained_generation_reports_nothing_unmet():
    """Nothing is pinned, so nothing can go unhonored: a rolled value that will
    not fit is a preference declined silently, never an unmet constraint."""
    for seed in range(20):
        assert generate_ship(RandomRolls.seeded(seed)).unmet == ()
        assert generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).unmet == ()


def test_result_equality_still_distinguishes_seeds():
    """The result record is compared, not just the ship it carries, so seeded
    reproducibility assertions keep their meaning after the return type change."""
    assert generate_ship(RandomRolls.seeded(42)) == generate_ship(RandomRolls.seeded(42))
    assert generate_ship(RandomRolls.seeded(1)) != generate_ship(RandomRolls.seeded(2))


# --- DesignConstraints: the referee's answers, carried as a value ---


def test_unconstrained_is_the_default_and_pins_nothing():
    """Constraints are optional, and their absence is `UNCONSTRAINED`.

    Every pin below is measured against this: the same seed with nothing pinned
    must still produce the ship it produced before constraints existed, which is
    what `tests/data/baseline/designs.json` holds.
    """
    for seed in range(20):
        assert generate_ship(RandomRolls.seeded(seed)) == generate_ship(
            RandomRolls.seeded(seed), constraints=UNCONSTRAINED
        )


def test_constraints_carry_the_hull_class_the_ruleset_branches_on():
    starship = generate_ship(RandomRolls.seeded(7)).ship
    small_craft = generate_ship(RandomRolls.seeded(7), constraints=_SMALL_CRAFT).ship

    assert starship.design.hull_class is HullClass.STARSHIP
    assert small_craft.design.hull_class is HullClass.SMALL_CRAFT


# --- Component families: a referee pins several, the dice still draw one ---


def _roomy(**constraints):
    """A 2000-ton hull, big enough that nothing here is declined on tonnage."""
    return generate_ship(
        RandomRolls.seeded(11), constraints=DesignConstraints(hull_tons=2000, **constraints)
    ).ship


def test_several_fittings_are_all_installed():
    """The question this whole change exists for: scoops *and* a processor, which
    the SRD treats as independent and which no single-valued field could express."""
    ship = _roomy(
        fittings=(FittingFit(kind="fuel_scoops"), FittingFit(kind="fuel_processor")),
    )

    assert [fit.kind for fit in ship.design.fittings] == ["fuel_scoops", "fuel_processor"]


def test_several_armor_layers_are_all_installed():
    layers = (
        ArmorFit(type=ArmorType.CRYSTALIRON, percent=10),
        ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),
    )
    ship = _roomy(armor=layers)

    assert ship.design.armor == layers


def test_several_screens_are_all_installed():
    ship = _roomy(screens=(ScreenFit(kind="meson_screen"), ScreenFit(kind="nuclear_damper")))

    assert [fit.kind for fit in ship.design.screens] == ["meson_screen", "nuclear_damper"]


def test_several_bays_are_all_installed_and_each_spends_a_hardpoint():
    ship = _roomy(bays=(BayFit(kind="meson"), BayFit(kind="fusion")))

    assert [fit.kind for fit in ship.design.bays] == ["meson", "fusion"]
    assert ship.hardpoints_used >= 2


def test_an_unaffordable_item_is_declined_by_name_while_the_rest_are_fitted():
    """A shortfall names the item, not the family: a referee who asks for three
    fittings and can have two needs to know *which* one was dropped."""
    result = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(
            hull_tons=100,
            fittings=(FittingFit(kind="armory"), FittingFit(kind="vault")),
        ),
    )

    fitted = [fit.kind for fit in result.ship.design.fittings]
    declined = [entry.asked for entry in result.unmet if entry.field == "fittings"]

    assert "armory" in fitted
    assert declined == ["vault"]


def test_bays_beyond_the_hardpoints_are_declined_one_by_one():
    result = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(
            hull_tons=200,  # two hardpoints
            turrets=(),
            bays=(BayFit(kind="fusion"), BayFit(kind="meson"), BayFit(kind="particle")),
        ),
    )

    declined = [entry for entry in result.unmet if entry.field == "bays"]

    assert len(result.ship.design.bays) < 3
    assert declined, "a bay with nowhere to go is a shortfall the referee hears about"


def test_an_unset_family_still_draws_at_most_one():
    """Pin-only plurality: roll plurality was considered and rejected, so a
    random ship is no busier than before. Swept over seeds because a single seed
    drawing one proves nothing about the next."""
    for seed in range(40):
        design = generate_ship(RandomRolls.seeded(seed)).ship.design
        assert len(design.armor) <= 1, seed
        assert len(design.fittings) <= 1, seed
        assert len(design.bays) <= 1, seed
        assert len(design.screens) <= 1, seed


def test_pinned_electronics_that_will_not_fit_are_declined():
    """The one scalar component whose three states are spelled out rather than
    shared with the families, so its shortfall path is worth its own case."""
    result = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT, hull_tons=10, electronics="very_advanced"
        ),
    )

    assert result.ship.design.electronics is None
    assert any(entry.field == "electronics" for entry in result.unmet)


# --- Three-state fields: unset rolls it, a value pins it, ABSENT pins its absence ---


_ROLLS_NO_ARMOR = 7
"""A seed whose 1200-ton ship draws no armor and has tonnage to spare, so armor
appearing on it can only be a pin."""

_ROLLS_ARMOR = 0
"""A seed whose ship draws crystaliron, so armor *not* appearing on it can only
be a pinned absence."""


def test_pinned_armor_is_installed_exactly_as_asked():
    pinned = ArmorFit(type=ArmorType.CRYSTALIRON, percent=10)

    rolled = generate_ship(RandomRolls.seeded(_ROLLS_NO_ARMOR)).ship
    result = generate_ship(
        RandomRolls.seeded(_ROLLS_NO_ARMOR), constraints=DesignConstraints(armor=(pinned,))
    )

    assert rolled.design.armor == ()
    assert result.ship.design.armor == (pinned,)


def test_absent_pins_an_unarmored_ship_where_chance_would_have_armored_it():
    """`ABSENT` is an answer, not an absence of one: the referee said no armor."""
    rolled = generate_ship(RandomRolls.seeded(_ROLLS_ARMOR)).ship
    result = generate_ship(
        RandomRolls.seeded(_ROLLS_ARMOR), constraints=DesignConstraints(armor=ABSENT)
    )

    assert rolled.design.armor != ()
    assert result.ship.design.armor == ()


def test_pinned_armor_options_are_installed_on_a_pinned_layer():
    result = generate_ship(
        RandomRolls.seeded(_ROLLS_NO_ARMOR),
        constraints=DesignConstraints(
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=10),),
            armor_options=("reflec", "stealth"),
        ),
    )

    assert result.ship.design.armor_options == ("reflec", "stealth")


def test_pinned_armor_options_are_dropped_and_recorded_when_no_armor_survives():
    """A coating needs armor beneath it, so pinning one beside a pinned *absence*
    of armor would hand `build_ship` a design its own rule refuses. The coatings
    are dropped and the referee is told, rather than half-obeyed in silence."""
    result = generate_ship(
        RandomRolls.seeded(_ROLLS_ARMOR),
        constraints=DesignConstraints(armor=ABSENT, armor_options=("reflec",)),
    )

    assert result.ship.design.armor_options == ()
    unmet = next(entry for entry in result.unmet if entry.field == "armor_options")
    assert unmet.asked == "reflec"
    assert unmet.reason == "no armor for them to coat"


def test_unset_armor_is_still_rolled():
    """The third state: nothing pinned, so the draw stands exactly as before."""
    for seed in range(20):
        assert generate_ship(RandomRolls.seeded(seed)) == generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(armor=None)
        )


def test_pinned_armor_may_be_a_type_the_generator_would_never_roll():
    """The curated list keeps *rolled* output plausible; it never bounds intent.

    Bonded superdense is absent from `_ARMOR_CHOICES`, so no seed can produce
    this ship by chance.
    """
    pinned = ArmorFit(type=ArmorType.BONDED_SUPERDENSE, percent=5)

    result = generate_ship(
        RandomRolls.seeded(_ROLLS_NO_ARMOR), constraints=DesignConstraints(armor=(pinned,))
    )

    assert result.ship.design.armor == (pinned,)
    assert pinned not in _ARMOR_CHOICES


def test_pinned_armor_draws_no_dice():
    """`ABSENT` pins the empty family and is not itself a layer, so it stands
    where the tuple would rather than inside one."""
    for pinned in ((ArmorFit(type=ArmorType.CRYSTALIRON, percent=10),), ABSENT):
        recorder = RecordingRolls(RandomRolls.seeded(_ROLLS_NO_ARMOR))
        generate_ship(recorder, constraints=DesignConstraints(armor=pinned))
        assert RollName.SHIP_ARMOR not in _names(recorder)


def test_pinned_armor_that_will_not_fit_leaves_the_ship_unarmored():
    """Generation never fails on tonnage. The shortfall is recorded for reporting;
    surfacing it on the result is #50's work."""
    result = generate_ship(
        RandomRolls.seeded(_ROLLS_NO_ARMOR),
        constraints=DesignConstraints(armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=100),)),
    )

    assert result.ship.design.armor == ()


# --- Drives are pinned as ratings, resolved to the lightest code delivering them ---


def test_pinned_jump_rating_installs_the_lightest_code_delivering_it():
    """A referee asks for Jump-2, not for drive C. Several codes deliver a rating
    on a hull; the lightest is chosen so the tonnage saved reaches the fuel."""
    hull_tons = 400
    result = generate_ship(
        RandomRolls.seeded(3),
        constraints=DesignConstraints(hull_tons=hull_tons, jump_rating=2),
    )
    ship = result.ship

    assert ship.jump_rating == 2
    assert ship.design.jump_code == min(
        (c for c, r in DRIVE_PERFORMANCE.items() if r.get(hull_tons) == 2),
        key=lambda c: DRIVE_COSTS[c].jump_tons,
    )


def test_pinned_maneuver_and_power_ratings_install_their_lightest_codes():
    hull_tons = 400
    result = generate_ship(
        RandomRolls.seeded(3),
        constraints=DesignConstraints(
            hull_tons=hull_tons, jump_rating=1, maneuver_rating=2, power_rating=3
        ),
    )
    ship = result.ship

    assert ship.maneuver_rating == 2
    assert ship.power_rating == 3
    assert ship.design.maneuver_code == min(
        (c for c, r in DRIVE_PERFORMANCE.items() if r.get(hull_tons) == 2),
        key=lambda c: DRIVE_COSTS[c].maneuver_tons,
    )
    assert ship.design.power_code == min(
        (c for c, r in DRIVE_PERFORMANCE.items() if r.get(hull_tons) == 3),
        key=lambda c: DRIVE_COSTS[c].power_tons,
    )


def test_pinned_ratings_draw_no_dice():
    recorder = RecordingRolls(RandomRolls.seeded(3))
    generate_ship(
        recorder,
        constraints=DesignConstraints(
            hull_tons=400, jump_rating=1, maneuver_rating=2, power_rating=3
        ),
    )

    assert RollName.SHIP_JUMP_CODE not in _names(recorder)
    assert RollName.SHIP_MANEUVER_CODE not in _names(recorder)
    assert RollName.SHIP_POWER_CODE not in _names(recorder)


def test_a_pinned_power_plant_caps_the_drives_left_to_chance():
    """A pinned plant is a promise; the drives left to chance are a preference.

    Jump and maneuver are drawn before the plant is resolved, so drawing them
    from every code the hull takes let the dice pick drives the pinned plant
    could not run and `build_ship` refused the design outright—a rolled
    preference invalidating a promise, which is the wrong way round. Rating 1
    is the weakest a 400-ton hull tabulates, so every seed here has somewhere
    to go wrong.
    """
    for seed in range(40):
        ship = generate_ship(
            RandomRolls.seeded(seed),
            constraints=DesignConstraints(hull_tons=400, power_rating=1),
        ).ship

        assert ship.power_rating == 1, seed
        assert max(ship.jump_rating, ship.maneuver_rating) <= 1, seed


def test_a_pinned_drive_above_a_pinned_plant_is_still_the_referee_s_to_make():
    """Capping applies to the dice, not to the referee. Two pins that contradict
    each other are a mistake `build_ship` owns the sentence for; the
    cap must not quietly rewrite one pin to suit the other."""
    with pytest.raises(ValueError, match="below required"):
        generate_ship(
            RandomRolls.seeded(3),
            constraints=DesignConstraints(hull_tons=400, jump_rating=4, power_rating=1),
        )


def test_a_rating_not_tabulated_for_the_hull_is_rejected():
    """Every starship hull happens to offer ratings 1-6 through some code, so the
    rejected answer here is one no hull can deliver at all."""
    with pytest.raises(ValueError, match="not tabulated for a 400-ton hull"):
        generate_ship(
            RandomRolls.seeded(3),
            constraints=DesignConstraints(hull_tons=400, jump_rating=9),
        )


def test_a_pinned_jump_rating_keeps_fuel_for_a_complete_jump():
    """The promise survives pinning: whatever rating ends up installed, the
    ship carries fuel for one full jump at it."""
    for seed in range(10):
        for rating in (1, 2):
            ship = generate_ship(
                RandomRolls.seeded(seed),
                constraints=DesignConstraints(hull_tons=400, jump_rating=rating),
            ).ship
            assert ship.assumed_jump_distance == ship.jump_rating
            assert ship.jump_fuel == pytest.approx(0.1 * ship.hull_tons * ship.jump_rating)


def test_a_jump_rating_the_hull_cannot_fuel_degrades_to_one_it_can():
    """The pin is a ceiling, not a promise the tonnage can keep: Jump-6 on a
    100-ton hull would need 60 tons of fuel on top of the drive. The ship still
    carries fuel for a full jump at whatever rating it ends up with, and the
    shortfall is recorded for reporting (#50)."""
    ship = generate_ship(
        RandomRolls.seeded(3),
        constraints=DesignConstraints(hull_tons=100, jump_rating=6),
    ).ship

    assert ship.jump_rating < 6
    assert ship.assumed_jump_distance == ship.jump_rating
    assert ship.tonnage_used <= ship.hull_tons


def test_available_ratings_widen_when_the_hull_is_unknown():
    """What the wizard can offer before the hull is drawn: every rating any hull
    of the class can deliver."""
    for hull_class in HullClass:
        widened = available_ratings(hull_class, None)
        for hull_tons in (HULLS if hull_class is HullClass.STARSHIP else SMALL_CRAFT_HULLS):
            assert set(available_ratings(hull_class, hull_tons)) <= set(widened)


def test_a_small_craft_rating_no_fitting_drive_delivers_degrades_and_is_recorded():
    """Tabulated for the hull, but nothing delivering it leaves room for the rest
    of the craft.

    That is a tonnage shortfall, so it degrades and is reported rather than
    refused (#50): the referee gets the best rating the hull can carry and is
    told it is not the one they asked for. This test asserted a refusal when
    #46 wrote it; #50 owns the rule that generation never raises on tonnage.
    """
    result = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT, hull_tons=10, maneuver_rating=6
        ),
    )

    assert result.ship.maneuver_rating < 6
    assert [(entry.field, entry.asked) for entry in result.unmet] == [("maneuver_rating", "6")]


def test_a_jump_rating_pinned_on_a_small_craft_is_rejected():
    """Legality the tables know at the point of input: small craft carry no jump
    drive, so the answer is refused rather than quietly ignored."""
    with pytest.raises(ValueError, match="small craft carry no jump drive"):
        generate_ship(
            RandomRolls.seeded(7),
            constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, jump_rating=1),
        )


def test_small_craft_honors_pinned_maneuver_and_power_ratings():
    """Seed 7 rolls a 1-G craft with a rating-2 plant on this hull, so 2 and 3
    are visibly the answers rather than the dice."""
    constraints = DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=40)
    rolled = generate_ship(RandomRolls.seeded(7), constraints=constraints).ship

    result = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=40,
            maneuver_rating=2,
            power_rating=3,
        ),
    )
    ship = result.ship

    assert (rolled.maneuver_rating, rolled.power_rating) == (1, 2)
    assert ship.maneuver_rating == 2
    assert ship.power_rating == 3


def test_small_craft_pinned_ratings_draw_no_dice():
    recorder = RecordingRolls(RandomRolls.seeded(7))
    generate_ship(
        recorder,
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=40,
            maneuver_rating=2,
            power_rating=3,
        ),
    )

    assert RollName.SHIP_MANEUVER_CODE not in _names(recorder)
    assert RollName.SHIP_POWER_CODE not in _names(recorder)


# --- The rest of the scalar surface: every field pins, rolls or is left absent ---

_PINS_AND_ROLLS = (
    ("configuration", Configuration.STREAMLINED, RollName.SHIP_CONFIGURATION),
    ("computer", ComputerFit(model=3), RollName.SHIP_COMPUTER),
    ("electronics", "basic_military", RollName.SHIP_ELECTRONICS),
    ("staterooms", 4, RollName.SHIP_STATEROOMS),
    ("fittings", (FittingFit(kind="laboratory"),), RollName.SHIP_FITTING),
    ("bays", (BayFit(kind="particle"),), RollName.SHIP_BAY),
    ("screens", (ScreenFit(kind="meson_screen"),), RollName.SHIP_SCREEN),
    ("name", "Wayfarer", RollName.SHIP_NAME),
)
"""Each constrainable field, a value to pin it to, and the draw it must displace."""


@pytest.mark.parametrize(
    "field,pinned,roll", _PINS_AND_ROLLS, ids=[f for f, _, _ in _PINS_AND_ROLLS]
)
def test_a_pinned_field_is_honored_and_draws_no_dice(field, pinned, roll):
    """One hull big enough for every pin here, so nothing is declined on tonnage."""
    recorder = RecordingRolls(RandomRolls.seeded(11))
    result = generate_ship(
        recorder,
        constraints=DesignConstraints(hull_tons=2000, **{field: pinned}),
    )

    assert roll not in _names(recorder)
    assert _installed(result.ship, field) == pinned


def _installed(ship, field):
    """What the finished design carries for `field`, in the shape it was pinned.

    The component families are pinned and carried as tuples, so they compare
    directly against the pin; the scalar fields are read as they always were.
    """
    return getattr(ship.design, field)


@pytest.mark.parametrize(
    "field,pinned,roll", _PINS_AND_ROLLS, ids=[f for f, _, _ in _PINS_AND_ROLLS]
)
def test_an_unset_field_is_still_rolled(field, pinned, roll):
    """The other half of the no-dice pin: left unset, the draw is still made.

    Without this, `test_a_pinned_field_is_honored_and_draws_no_dice` would pass
    just as well if the roll had been deleted outright.
    """
    recorder = RecordingRolls(RandomRolls.seeded(11))
    generate_ship(recorder, constraints=DesignConstraints(hull_tons=2000, **{field: None}))

    assert roll in _names(recorder)


@pytest.mark.parametrize("field", ["computer", "electronics", "fittings", "bays", "screens"])
def test_absent_pins_an_optional_component_away(field):
    result = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(hull_tons=2000, **{field: ABSENT}),
    )

    # A family pins away to the empty tuple; a scalar component to `None`.
    assert _installed(result.ship, field) in (None, ())


def test_a_pinned_stateroom_count_of_zero_is_honored():
    """Zero is an answer, not a missing one: `None` rolls, `0` pins an empty ship."""
    rolled = generate_ship(RandomRolls.seeded(11), constraints=DesignConstraints(hull_tons=2000))
    pinned = generate_ship(
        RandomRolls.seeded(11), constraints=DesignConstraints(hull_tons=2000, staterooms=0)
    )

    assert rolled.ship.design.staterooms > 0
    assert pinned.ship.design.staterooms == 0


def test_absent_pins_a_ship_with_no_name_of_its_own():
    """A blank name is *no* name, which the renderer already understands, and is
    a different answer from letting the catalog supply one."""
    rolled = generate_ship(RandomRolls.seeded(11)).ship
    pinned = generate_ship(RandomRolls.seeded(11), constraints=DesignConstraints(name=ABSENT)).ship

    assert rolled.design.name in _CATALOG_NAMES
    assert pinned.design.name == ""


def test_a_bay_pinned_on_a_small_craft_is_rejected():
    """Small craft forbid bays outright, which the tables know at input."""
    with pytest.raises(ValueError, match="small craft carry no weapon bays"):
        generate_ship(
            RandomRolls.seeded(7),
            constraints=DesignConstraints(
                hull_class=HullClass.SMALL_CRAFT, bays=(BayFit(kind="particle"),)
            ),
        )


def test_a_screen_pinned_on_a_small_craft_is_fitted():
    """Never rolled onto a small craft, but the rules permit one, so a pinned
    screen is fitted rather than silently dropped."""
    pinned = ScreenFit(kind="nuclear_damper")

    result = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=95,
            # A screen is 50 tons, which only the largest craft with the
            # smallest drives can spare; the rest of the budget is cleared so
            # this tests the wiring rather than the arithmetic.
            maneuver_rating=1,
            power_rating=1,
            armor=ABSENT,
            fittings=ABSENT,
            staterooms=0,
            screens=(pinned,),
        ),
    )

    assert result.ship.design.screens == (pinned,)


def test_an_unset_screen_is_never_rolled_onto_a_small_craft():
    """Honoring a pinned screen must not have turned screens into a draw."""
    for seed in range(20):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        result = generate_ship(recorder, constraints=_SMALL_CRAFT)

        assert RollName.SHIP_SCREEN not in _names(recorder)
        assert result.ship.design.screens == ()


def test_purpose_is_never_rolled_and_is_carried_when_pinned():
    """The one field generation does not invent: unanswered leaves it unset."""
    rolled = generate_ship(RandomRolls.seeded(11)).ship
    pinned = generate_ship(
        RandomRolls.seeded(11), constraints=DesignConstraints(purpose="a courier for the mails")
    ).ship

    assert rolled.design.purpose is None
    assert pinned.design.purpose == "a courier for the mails"


def test_a_pinned_stateroom_count_the_budget_cannot_cover_is_clamped():
    """The referee asked for rooms, not for a specific ship, so an unaffordable
    count is clamped like a drawn one rather than refused."""
    ship = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(hull_tons=100, staterooms=100),
    ).ship

    assert 0 <= ship.design.staterooms < 100
    assert ship.tonnage_used <= ship.hull_tons


def test_a_pinned_bay_with_no_hardpoint_left_is_declined():
    """Seed 0 spends this hull's single hardpoint on a turret, so the bay has
    nowhere to mount even though the tonnage might have covered it."""
    ship = generate_ship(
        RandomRolls.seeded(0),
        constraints=DesignConstraints(hull_tons=100, bays=(BayFit(kind="missile_bank"),)),
    ).ship

    assert ship.design.turrets
    assert ship.design.bays == ()


def test_a_pinned_bay_the_budget_cannot_cover_is_declined():
    """A hardpoint free to mount it on, but not the 51 tons it needs.

    Jump-3 and 15% crystaliron between them leave this hull under the bay's
    tonnage, which is a different shortfall from having nowhere to mount it.
    """
    ship = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(
            hull_tons=300,
            jump_rating=3,
            staterooms=0,
            fittings=ABSENT,
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=15),),
            bays=(BayFit(kind="particle"),),
        ),
    ).ship

    assert ship.hardpoints > len(ship.design.turrets)  # a hardpoint was free
    assert ship.design.bays == ()


def test_a_pinned_component_may_be_one_the_generator_would_never_roll():
    """The curated lists bound rolled output, never intent."""
    pinned = FittingFit(kind="vehicle_hangar", vehicle_tons=20)

    result = generate_ship(
        RandomRolls.seeded(11), constraints=DesignConstraints(hull_tons=2000, fittings=(pinned,))
    )

    assert result.ship.design.fittings == (pinned,)
    assert "vehicle_hangar" not in _FITTING_CHOICES


# --- Turrets: a count, and per turret a mount and a weapon ---


def test_a_pinned_turret_count_of_zero_leaves_the_ship_unarmed():
    """Zero is an answer: `None` rolls a count, `()` pins an unarmed ship."""
    rolled = generate_ship(
        RandomRolls.seeded(0), constraints=DesignConstraints(hull_tons=400)
    ).ship
    pinned = generate_ship(
        RandomRolls.seeded(0), constraints=DesignConstraints(hull_tons=400, turrets=())
    ).ship

    assert rolled.design.turrets != ()
    assert pinned.design.turrets == ()


def test_a_pinned_count_alone_fits_that_many_turrets_and_rolls_their_details():
    """Count-only: the inner questions were skipped, so mount and weapon still draw."""
    recorder = RecordingRolls(RandomRolls.seeded(11))
    result = generate_ship(
        recorder,
        constraints=DesignConstraints(hull_tons=2000, turrets=(TurretPin(), TurretPin())),
    )

    assert len(result.ship.design.turrets) == 2
    assert RollName.SHIP_TURRET_COUNT not in _names(recorder)
    assert _names(recorder).count(RollName.SHIP_TURRET_MOUNT) == 2
    assert _names(recorder).count(RollName.SHIP_WEAPON) == 2


def test_a_pinned_mount_and_weapon_are_fitted_and_draw_no_dice():
    recorder = RecordingRolls(RandomRolls.seeded(11))
    result = generate_ship(
        recorder,
        constraints=DesignConstraints(
            hull_tons=2000,
            turrets=(TurretPin(mount="triple", weapon="pulse_laser"),),
        ),
    )

    (turret,) = result.ship.design.turrets
    assert turret.mount == "triple"
    assert turret.weapons == ("pulse_laser",) * 3
    assert RollName.SHIP_TURRET_MOUNT not in _names(recorder)
    assert RollName.SHIP_WEAPON not in _names(recorder)


def test_a_pinned_weapon_may_ride_a_rolled_mount_and_the_reverse():
    """Each half of a turret is answered on its own."""
    weapon_only = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(hull_tons=2000, turrets=(TurretPin(weapon="sandcaster"),)),
    ).ship
    mount_only = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(hull_tons=2000, turrets=(TurretPin(mount="pop_up"),)),
    ).ship

    (weapon_turret,) = weapon_only.design.turrets
    (mount_turret,) = mount_only.design.turrets
    assert set(weapon_turret.weapons) == {"sandcaster"}
    assert mount_turret.mount == "pop_up"


def test_a_turret_count_above_the_hulls_hardpoints_is_rejected():
    """Hardpoints follow from the hull, which is settled before turrets are asked."""
    with pytest.raises(ValueError, match="a 100-ton starship has 1 hardpoint"):
        generate_ship(
            RandomRolls.seeded(11),
            constraints=DesignConstraints(hull_tons=100, turrets=(TurretPin(), TurretPin())),
        )


def test_a_pinned_turret_the_budget_cannot_cover_is_declined():
    """A hardpoint to mount it on, but no tonnage left to put in it."""
    ship = generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(
            hull_tons=200,
            jump_rating=2,
            # 45% of a 200-ton hull is 90 tons of crystaliron, which fits and
            # leaves nothing behind it for even a 2-ton pop-up turret.
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=45),),
            staterooms=0,
            fittings=ABSENT,
            turrets=(TurretPin(mount="pop_up", weapon="pulse_laser"),),
        ),
    ).ship

    assert ship.hardpoints >= 1
    assert ship.design.turrets == ()


def test_a_small_craft_honors_a_pinned_turret_on_its_single_hardpoint():
    """The smaller ruleset takes its own path, but an answer is still an answer."""
    result = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=95,
            turrets=(TurretPin(mount="single", weapon="sandcaster"),),
        ),
    )

    (turret,) = result.ship.design.turrets
    assert (turret.mount, turret.weapons) == ("single", ("sandcaster",))


def test_a_pinned_multi_slot_mount_caps_the_weapon_left_to_chance():
    """A mount carries the same weapon in every slot, so the plant's allowance is
    what three slots ask for, not one.

    `_SMALL_CRAFT_TURRET_MOUNTS` holds only single-slot mounts, so a *drawn*
    mount can never ask for more than one energy weapon—but a *pinned* triple
    can, and the weapon was still drawn on whether the plant ran any energy
    weapon at all. The pin was legal and the roll broke it, which is the wrong
    way round.
    """
    for seed in range(40):
        ship = generate_ship(
            RandomRolls.seeded(seed),
            constraints=DesignConstraints(
                hull_class=HullClass.SMALL_CRAFT,
                hull_tons=50,
                turrets=(TurretPin(mount="triple"),),
            ),
        ).ship

        for turret in ship.design.turrets:
            energy = sum(TURRET_WEAPONS[weapon].energy for weapon in turret.weapons)
            assert energy <= SMALL_CRAFT_ENERGY_CAPS[ship.design.power_code[1:]], seed


def test_a_small_craft_pinned_to_no_turrets_is_unarmed():
    """Seed 4 arms this craft, so an unarmed one here can only be the answer."""
    constraints = DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=95)
    rolled = generate_ship(RandomRolls.seeded(4), constraints=constraints).ship
    pinned = generate_ship(
        RandomRolls.seeded(4),
        constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=95, turrets=()),
    ).ship

    assert rolled.design.turrets != ()
    assert pinned.design.turrets == ()


def test_a_small_craft_turret_the_budget_cannot_cover_is_not_fitted():
    """A 20-ton hull with armor on it has a hardpoint but no tonnage behind it.

    The record of the shortfall is written to the ledger, which nothing reads
    until #50; what is observable here is that the craft still builds.
    """
    ship = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=20,
            staterooms=0,
            fittings=ABSENT,
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),),
            turrets=(TurretPin(mount="pop_up", weapon="sandcaster"),),
        ),
    ).ship

    assert ship.design.turrets == ()
    assert ship.tonnage_used <= ship.hull_tons


def test_a_small_craft_has_one_hardpoint_however_small_it_is():
    """Counted by the starship rule a 40-ton launch would have none at all."""
    with pytest.raises(ValueError, match="a 40-ton small craft has 1 hardpoint"):
        generate_ship(
            RandomRolls.seeded(7),
            constraints=DesignConstraints(
                hull_class=HullClass.SMALL_CRAFT,
                hull_tons=40,
                turrets=(TurretPin(), TurretPin()),
            ),
        )

    fitted = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT, hull_tons=40, turrets=(TurretPin(),)
        ),
    ).ship
    assert len(fitted.design.turrets) == 1


def test_unset_turrets_are_still_rolled():
    for seed in range(20):
        assert generate_ship(RandomRolls.seeded(seed)) == generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(turrets=None)
        )


# --- Unmet constraints reach the caller (#50) ---


def _overloaded() -> GenerationResult:
    """A 200-ton hull asked for more than it can hold.

    Jump-2 and 30% crystaliron take most of the hull between them, leaving room
    for seven of the eight staterooms and neither turret. The ticket's own
    example (six staterooms, 20% armor) turns out to *fit* with 22 tons spare,
    which is why the numbers here are larger than the prose suggests.
    """
    return generate_ship(
        RandomRolls.seeded(11),
        constraints=DesignConstraints(
            hull_tons=200,
            jump_rating=2,
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=30),),
            staterooms=8,
            turrets=(
                TurretPin(mount="triple", weapon="pulse_laser"),
                TurretPin(mount="triple", weapon="pulse_laser"),
            ),
        ),
    )


def test_a_pinned_value_that_will_not_fit_is_reported_on_the_result():
    result = _overloaded()

    assert result.unmet != ()
    assert all(isinstance(entry, UnmetConstraint) for entry in result.unmet)


def test_an_unmet_constraint_carries_the_field_what_was_asked_what_was_got_and_why():
    """A library caller reads the record; nobody should parse a sentence."""
    result = _overloaded()

    assert [(entry.field, entry.asked, entry.got) for entry in result.unmet] == [
        ("staterooms", "8", "7"),
        ("turrets", "turret 1 (triple pulse_laser)", "none"),
        ("turrets", "turret 2 (triple pulse_laser)", "none"),
    ]
    assert result.unmet[0].reason == "needs 32t, 30t free"

    # Every `field` names an attribute a caller can match on the constraints.
    known = {field.name for field in fields(DesignConstraints)}
    assert all(entry.field in known for entry in result.unmet)


def test_generation_still_yields_a_ship_when_constraints_go_unmet():
    """Never fails on tonnage: a real, legal ship comes back regardless."""
    result = _overloaded()

    assert result.ship.hull_tons == 200
    assert result.ship.tonnage_used <= result.ship.hull_tons


def test_a_rolled_value_that_will_not_fit_is_still_declined_silently():
    """A preference, not a promise: a sweep with nothing pinned reports nothing,
    including the many seeds whose drawn components do not all fit."""
    for seed in range(200):
        assert generate_ship(RandomRolls.seeded(seed)).unmet == ()
        assert generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).unmet == ()


def test_a_small_craft_reports_its_unmet_constraints_too():
    """The smaller ruleset takes its own path; the report must come back from it."""
    result = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=20,
            staterooms=0,
            fittings=ABSENT,
            armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),),
            turrets=(TurretPin(mount="pop_up", weapon="sandcaster"),),
        ),
    )

    assert [entry.field for entry in result.unmet] == ["turrets"]


# --- What a small-craft session may offer (#49) ---


def test_small_craft_power_ratings_are_those_a_pinned_maneuver_leaves_room_for():
    """The pair is chosen jointly on this path, so a maneuver pin narrows what
    the power plant can still be: never below it, and never so heavy that the
    two together leave no room for a cockpit.

    A 15-ton hull is the clearest case. It can deliver ratings 1 through 6
    through some drive, but a craft already carrying a 1-G maneuver drive has
    room for a plant at only 1 or 2.
    """
    offered = small_craft_power_ratings(hull_tons=15, maneuver_rating=1)

    assert offered == (1, 2)
    assert set(offered) < set(available_ratings(HullClass.SMALL_CRAFT, 15))


def test_small_craft_power_ratings_narrow_as_the_maneuver_pin_rises():
    generous = small_craft_power_ratings(hull_tons=15, maneuver_rating=1)
    demanding = small_craft_power_ratings(hull_tons=15, maneuver_rating=2)

    assert generous == (1, 2)
    assert demanding == (2,)


def test_a_pinned_power_rating_a_maneuver_pin_forbids_is_reported():
    """Offered and honored agree: a rating this helper omits does not generate,
    and the referee is told so rather than quietly given something else."""
    forbidden = [
        rating
        for rating in available_ratings(HullClass.SMALL_CRAFT, 15)
        if rating not in small_craft_power_ratings(hull_tons=15, maneuver_rating=1)
    ]
    assert forbidden

    for rating in forbidden:
        result = generate_ship(
            RandomRolls.seeded(7),
            constraints=DesignConstraints(
                hull_class=HullClass.SMALL_CRAFT,
                hull_tons=15,
                maneuver_rating=1,
                power_rating=rating,
            ),
        )
        assert [entry.field for entry in result.unmet] == ["power_rating"], rating


def test_a_power_rating_raised_to_meet_its_drive_is_told_which_rule_raised_it():
    """A pin that comes back *higher* than asked did not run out of tonnage.

    Drive A delivers rating 1 on a 15-ton hull and is the lightest code there, so
    "no power drive delivering 1 fits" was a tonnage story about a rules
    constraint: a plant may not be rated below the drive it powers. The referee
    reads this reason to decide what to revise, and the CLI was offering to
    revise a field that had come back better than asked.
    """
    result = generate_ship(
        RandomRolls.seeded(3),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=15,
            maneuver_rating=2,
            power_rating=1,
        ),
    )

    (unmet,) = result.unmet
    assert (unmet.field, unmet.asked, unmet.got) == ("power_rating", "1", "2")
    assert unmet.reason == "a power plant may not be rated below the Maneuver-2 drive it powers"


def test_small_craft_maneuver_ratings_are_those_the_craft_can_carry():
    """Narrower than the drive table: a rating whose every drive leaves no room
    for a plant beside it is not one this craft can have."""
    carryable = small_craft_maneuver_ratings(40)

    assert set(carryable) < set(available_ratings(HullClass.SMALL_CRAFT, 40))
    assert all(small_craft_power_ratings(40, rating) for rating in carryable)


def test_a_pinned_energy_weapon_the_plant_cannot_run_is_reported_not_raised():
    """The plant is only known once chosen, so a weapon it cannot run is
    declined there. `build_ship` would refuse the design and cost the session
    its ship; a craft with no turret is still a craft."""
    result = generate_ship(
        RandomRolls.seeded(7),
        constraints=DesignConstraints(
            hull_class=HullClass.SMALL_CRAFT,
            hull_tons=40,
            maneuver_rating=1,
            power_rating=1,
            turrets=(TurretPin(mount="single", weapon="pulse_laser"),),
        ),
    )

    assert result.ship.design.turrets == ()
    assert [entry.field for entry in result.unmet] == ["turrets"]
    assert "energy weapon" in result.unmet[0].reason


def test_a_small_craft_plant_with_no_energy_allowance_forbids_an_energy_weapon():
    """The weapon a small craft may carry is capped by its power plant, so the
    check needs the plant the pinned rating resolves to."""
    with pytest.raises(ValueError, match="runs 0 energy weapon"):
        validate_small_craft_weapon(hull_tons=40, power_rating=1, weapon="pulse_laser")


def test_a_small_craft_plant_with_an_allowance_permits_an_energy_weapon():
    allowance = next(
        rating
        for rating in available_ratings(HullClass.SMALL_CRAFT, 40)
        if _energy_allowance(40, rating)
    )

    validate_small_craft_weapon(hull_tons=40, power_rating=allowance, weapon="pulse_laser")


def test_a_non_energy_weapon_needs_no_allowance():
    for rating in available_ratings(HullClass.SMALL_CRAFT, 40):
        validate_small_craft_weapon(hull_tons=40, power_rating=rating, weapon="sandcaster")


# --- ScriptedRolls pins a known component selection to an exact Ship ---


def test_scripted_rolls_all_defaults_yields_exact_ship():
    ship = generate_ship(ScriptedRolls()).ship

    assert ship.hull_tons == 100
    assert ship.jump_rating == 2
    assert ship.maneuver_rating == 2
    assert ship.power_rating == 2
    assert ship.assumed_jump_distance == 2
    assert ship.jump_fuel == pytest.approx(20.0)
    assert ship.power_fuel == pytest.approx(2.0)
    assert ship.tonnage_used == pytest.approx(48.0)
    assert ship.cargo_tons == pytest.approx(52.0)
    assert ship.hull_points == 2
    assert ship.structure_points == 2
    assert ship.hardpoints == 1
    assert ship.hardpoints_used == 0
    assert ship.build_weeks == HULLS[100].build_weeks

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 1
    assert crew.gunners == 0
    assert crew.screen_operators == 0
    assert crew.medic == 0
    assert crew.stewards == 0


# --- reproducibility ---


def test_random_rolls_seeded_reproducible():
    a = generate_ship(RandomRolls.seeded(42)).ship
    b = generate_ship(RandomRolls.seeded(42)).ship
    assert a == b


def test_random_rolls_different_seeds_can_differ():
    a = generate_ship(RandomRolls.seeded(1)).ship
    b = generate_ship(RandomRolls.seeded(2)).ship
    assert a != b


# --- a sweep of many seeds never raises ---


def test_many_seeds_all_produce_ships():
    for seed in range(200):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert ship.cargo_tons >= 0


# --- a pinned hull tonnage is honored ---


def test_hull_size_is_honored():
    for seed in range(20):
        ship = generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=400)
        ).ship
        assert ship.hull_tons == 400


def test_unknown_hull_size_raises():
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        generate_ship(RandomRolls.seeded(1), constraints=DesignConstraints(hull_tons=150))


# --- generated ships round-trip losslessly ---


def test_generated_ships_round_trip():
    for seed in range(20):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert build_ship(loads_design(dump_design(ship.design))) == ship


def test_default_rolls_is_random_rolls():
    # No explicit `rolls` argument still produces a valid ship (defaults to RandomRolls()).
    ship = generate_ship().ship
    assert ship.cargo_tons >= 0


# --- every generated ship is named ---


def test_generated_starship_carries_a_catalog_name():
    ship = generate_ship(RandomRolls.seeded(42)).ship
    assert ship.design.name in _CATALOG_NAMES


def test_generated_small_craft_carries_a_catalog_name():
    ship = generate_ship(RandomRolls.seeded(7), constraints=_SMALL_CRAFT).ship
    assert ship.design.name in _CATALOG_NAMES


# --- naming is reproducible by seed, not forced across seeds ---


def test_generated_ship_name_is_reproducible_from_a_seed():
    a = generate_ship(RandomRolls.seeded(42)).ship
    b = generate_ship(RandomRolls.seeded(42)).ship
    assert a == b
    assert a.design.name == b.design.name


def test_generated_ship_names_across_seeds_are_not_forced_to_match():
    names = {generate_ship(RandomRolls.seeded(seed)).ship.design.name for seed in range(20)}
    assert len(names) > 1


# --- generated batches read as varied ---
# Pinned seed set 0-19 so this check cannot flake.


def test_generated_ships_over_a_pinned_seed_set_are_mostly_distinct():
    names = [generate_ship(RandomRolls.seeded(seed)).ship.design.name for seed in range(20)]
    assert len(set(names)) >= 17


# --- small craft (SRD "Small Craft Design") ---


def test_small_craft_yields_a_10_to_95_ton_ship_with_no_jump_drive():
    for seed in range(200):
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert 10 <= ship.hull_tons <= 95
        assert ship.jump_rating == 0
        assert ship.jump_fuel == pytest.approx(0.0)
        assert ship.cargo_tons >= 0


def test_small_craft_reproducible_from_a_seed():
    a = generate_ship(RandomRolls.seeded(42), constraints=_SMALL_CRAFT).ship
    b = generate_ship(RandomRolls.seeded(42), constraints=_SMALL_CRAFT).ship
    assert a == b


def test_small_craft_hull_size_is_honored():
    for tons in (10, 40, 95):
        for seed in range(10):
            ship = generate_ship(
                RandomRolls.seeded(seed),
                constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=tons),
            ).ship
            assert ship.hull_tons == tons


def test_small_craft_unknown_hull_size_raises():
    with pytest.raises(ValueError, match="not a tabulated small-craft hull size"):
        generate_ship(
            RandomRolls.seeded(1),
            constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=100),
        )


def test_small_craft_round_trips_losslessly():
    for seed in range(50):
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert build_ship(loads_design(dump_design(ship.design))) == ship


# --- bays and screens (SRD "Bays", "Screens") ---


def test_generated_bays_never_exceed_hardpoints_or_free_tonnage():
    for seed in range(300):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert ship.hardpoints_used <= ship.hardpoints
        assert ship.cargo_tons >= 0


def test_generated_ships_never_carry_a_bay_on_small_craft():
    for seed in range(300):
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert ship.design.bays == ()


def test_a_bay_is_reachable_for_a_large_enough_hull():
    # Sweep enough seeds on a hull with ample hardpoints and tonnage that at
    # least one draw selects a bay (bay selection is randomized, not forced).
    assert any(
        generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=2000)
        ).ship.design.bays
        for seed in range(300)
    )


def test_a_screen_is_reachable_for_a_large_enough_hull():
    assert any(
        generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=2000)
        ).ship.design.screens
        for seed in range(300)
    )


# --- Phase 2 Foundational: `_fit_jump_drive` ---
# Contract tests C1-C4/C8, driven by four worked examples.
# These were written before `_fit_jump_drive` existed and confirmed red against
# the AttributeError it raised then; the implementation followed, and they have
# passed since.

_FIT_WORKED_EXAMPLES = (
    (400, "C", 200, "B"),
    (700, "Z", 600, "U"),
    (700, "Z", 400, "N"),
    (100, "C", 72, "B"),
)


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_matches_the_contracts_worked_examples(
    hull_tons, drawn_code, budget, expected
):
    from cetools.engine.ships.generator import _fit_jump_drive

    assert _fit_jump_drive(hull_tons, drawn_code, budget) == expected


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c1_result_is_legal_for_the_hull(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    assert hull_tons in DRIVE_PERFORMANCE[result]


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c2_rating_is_never_raised(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    assert DRIVE_PERFORMANCE[result][hull_tons] <= DRIVE_PERFORMANCE[drawn_code][hull_tons]


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c3_result_is_the_unique_lightest_at_its_rating(
    hull_tons, drawn_code, budget, expected
):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    result_rating = DRIVE_PERFORMANCE[result][hull_tons]
    result_tons = DRIVE_COSTS[result].jump_tons
    for code, ratings in DRIVE_PERFORMANCE.items():
        if hull_tons in ratings and ratings[hull_tons] == result_rating:
            assert DRIVE_COSTS[code].jump_tons >= result_tons


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c4_highest_affordable_rating_wins(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    ceiling = DRIVE_PERFORMANCE[drawn_code][hull_tons]
    affordable_ratings = [
        ratings[hull_tons]
        for code, ratings in DRIVE_PERFORMANCE.items()
        if hull_tons in ratings
        and ratings[hull_tons] <= ceiling
        and DRIVE_COSTS[code].jump_tons + 0.1 * hull_tons * ratings[hull_tons] <= budget
    ]
    result_rating = DRIVE_PERFORMANCE[result][hull_tons]
    if affordable_ratings:
        assert result_rating == max(affordable_ratings)
        assert DRIVE_COSTS[result].jump_tons + 0.1 * hull_tons * result_rating <= budget
    else:
        assert result_rating == min(
            ratings[hull_tons]
            for code, ratings in DRIVE_PERFORMANCE.items()
            if hull_tons in ratings
        )


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c8_is_idempotent(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    assert _fit_jump_drive(hull_tons, result, budget) == result


def test_fit_jump_drive_legality_and_ceiling_hold_over_every_hull_and_legal_drawn_code():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        for drawn_code, ratings in DRIVE_PERFORMANCE.items():
            if hull_tons not in ratings:
                continue
            result = _fit_jump_drive(hull_tons, drawn_code, 10_000.0)
            assert hull_tons in DRIVE_PERFORMANCE[result]
            assert DRIVE_PERFORMANCE[result][hull_tons] <= ratings[hull_tons]


# C3 and C4 swept over every hull, every legal drawn code and a spread of
# budgets, matching the coverage C1/C2 (above) and C5/C6 (below) already have.
# Postconditions C1-C8 are the acceptance criteria for this function's tests;
# C3 and C4 alone were still example-driven.

_FIT_SWEEP_BUDGETS = (0.0, 1.0, 5.0, 20.0, 55.0, 72.0, 100.0, 200.0, 400.0, 600.0, 10_000.0)


def test_fit_jump_drive_c3_is_the_lightest_at_its_rating_over_every_hull_and_budget():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        for drawn_code in legal:
            for budget in _FIT_SWEEP_BUDGETS:
                result = _fit_jump_drive(hull_tons, drawn_code, budget)
                result_rating = DRIVE_PERFORMANCE[result][hull_tons]
                result_tons = DRIVE_COSTS[result].jump_tons
                for code in legal:
                    if DRIVE_PERFORMANCE[code][hull_tons] == result_rating:
                        assert DRIVE_COSTS[code].jump_tons >= result_tons


def test_fit_jump_drive_c4_highest_affordable_rating_wins_over_every_hull_and_budget():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        lowest_rating = min(DRIVE_PERFORMANCE[code][hull_tons] for code in legal)
        for drawn_code in legal:
            ceiling = DRIVE_PERFORMANCE[drawn_code][hull_tons]
            for budget in _FIT_SWEEP_BUDGETS:
                result = _fit_jump_drive(hull_tons, drawn_code, budget)
                result_rating = DRIVE_PERFORMANCE[result][hull_tons]
                affordable = [
                    DRIVE_PERFORMANCE[code][hull_tons]
                    for code in legal
                    if DRIVE_PERFORMANCE[code][hull_tons] <= ceiling
                    and DRIVE_COSTS[code].jump_tons
                    + 0.1 * hull_tons * DRIVE_PERFORMANCE[code][hull_tons]
                    <= budget
                ]
                if affordable:
                    assert result_rating == max(affordable)
                    assert (
                        DRIVE_COSTS[result].jump_tons + 0.1 * hull_tons * result_rating <= budget
                    )
                else:
                    assert result_rating == lowest_rating


# The starved-hull fallback (contract C5, C6), tested against the
# helper directly since no seed can reach it through `generate_ship`.


def test_fit_jump_drive_c5_starved_hull_falls_back_to_the_lowest_rated_legal_drive():
    from cetools.engine.ships.generator import _fit_jump_drive

    assert _fit_jump_drive(100, "A", 5.0) == "A"


def test_fit_jump_drive_c5_zero_budget_falls_back_to_the_lightest_lowest_rated_drive():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        drawn_code = max(legal, key=lambda code: DRIVE_PERFORMANCE[code][hull_tons])

        result = _fit_jump_drive(hull_tons, drawn_code, 0.0)

        lowest_rating = min(DRIVE_PERFORMANCE[code][hull_tons] for code in legal)
        lightest_at_lowest = min(
            (code for code in legal if DRIVE_PERFORMANCE[code][hull_tons] == lowest_rating),
            key=lambda code: DRIVE_COSTS[code].jump_tons,
        )
        assert result == lightest_at_lowest


def test_fit_jump_drive_c6_never_raises_for_any_input_satisfying_the_preconditions():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        for drawn_code, ratings in DRIVE_PERFORMANCE.items():
            if hull_tons not in ratings:
                continue
            for budget in (0.0, 1.0, 50.0, 10_000.0):
                _fit_jump_drive(hull_tons, drawn_code, budget)


# --- Phase 3, User Story 1: every generated starship can make at least one
# jump. These tests were written and confirmed red before `generate_ship`'s
# allocation was reordered to satisfy them.


def _fr014_budget_tons(ship) -> float:
    """Recompute the mandatory-systems tonnage budget from a *finished* ship's
    own hull, maneuver drive and power plant, so the starved-hull
    classification below depends on nothing internal to the generator."""
    from cetools.engine.ships.generator import _bridge_tons

    maneuver_tons = DRIVE_COSTS[ship.design.maneuver_code].maneuver_tons
    power_tons = DRIVE_COSTS[ship.design.power_code].power_tons
    power_fuel_tons = (power_tons // 3) * 2
    bridge_tons = _bridge_tons(ship.hull_tons)
    return ship.hull_tons - (maneuver_tons + power_tons + bridge_tons + power_fuel_tons)


def _is_fr014_starved_hull_ship(ship) -> bool:
    """A ship is a starved-hull ship exactly when its jump fuel falls short of
    one complete jump at its installed rating *and* no drive legal for its
    hull could have been fueled for one complete jump within its own tonnage
    budget — both halves recomputable from the finished
    ship rather than from generator internals."""
    if ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating:
        return False
    budget = _fr014_budget_tons(ship)
    legal = [c for c, ratings in DRIVE_PERFORMANCE.items() if ship.hull_tons in ratings]
    return not any(
        DRIVE_COSTS[c].jump_tons + 0.1 * ship.hull_tons * DRIVE_PERFORMANCE[c][ship.hull_tons]
        <= budget
        for c in legal
    )


def test_sc001_sc002_every_generated_starship_carries_fuel_for_one_full_jump():
    starved = 0
    for seed in range(2000):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        if _is_fr014_starved_hull_ship(ship):
            starved += 1
            continue
        assert ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating
        assert ship.assumed_jump_distance == ship.jump_rating
    assert starved == 0


def test_us1_as1_a_100_ton_hull_with_maneuver_a_and_power_c_mounts_jump_b_at_jump_4():
    # Overview scenario / contracts worked example 4: 100/C/72 -> B (Jump-4).
    # 72 tons remain for the jump drive once the 10-ton bridge, 2-ton maneuver
    # drive, 10-ton power plant and 6 tons of power-plant fuel are deducted.
    from cetools.engine.ships.generator import _codes_valid_for_hull

    hull_tons = 100
    valid = _codes_valid_for_hull(hull_tons)
    jump_index = valid.index("C")
    maneuver_index = valid.index("A")
    required = max(DRIVE_PERFORMANCE["C"][hull_tons], DRIVE_PERFORMANCE["A"][hull_tons])
    power_candidates = [c for c in valid if DRIVE_PERFORMANCE[c][hull_tons] >= required]
    power_index = power_candidates.index("C")

    rolls = ScriptedRolls(
        choices={
            RollName.SHIP_JUMP_CODE: jump_index,
            RollName.SHIP_MANEUVER_CODE: maneuver_index,
            RollName.SHIP_POWER_CODE: power_index,
        }
    )
    ship = generate_ship(rolls, constraints=DesignConstraints(hull_tons=hull_tons)).ship

    assert ship.design.jump_code == "B"
    assert ship.jump_rating == 4
    assert ship.assumed_jump_distance == 4
    assert ship.jump_fuel == pytest.approx(40.0)


def test_sc007_ships_already_fully_fueled_before_the_change_keep_their_rating():
    with open(_PRE_CHANGE_SWEEP_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)["standard"]

    checked = 0
    for seed_text, before in baseline.items():
        if before["assumed_jump_distance"] != before["jump_rating"]:
            continue
        seed = int(seed_text)
        ship = generate_ship(RandomRolls.seeded(seed)).ship

        assert ship.hull_tons == before["hull_tons"]
        assert ship.jump_rating == before["jump_rating"]
        assert ship.design.maneuver_code == before["maneuver_code"]
        assert ship.design.power_code == before["power_code"]
        if ship.design.jump_code != before["jump_code"]:
            before_tons = DRIVE_COSTS[before["jump_code"]].jump_tons
            after_tons = DRIVE_COSTS[ship.design.jump_code].jump_tons
            assert after_tons < before_tons
        checked += 1
    assert checked > 0


def test_sc003_allocated_tonnage_never_overruns_the_hull():
    # Build validation's other half — "passes exactly the same validation a
    # caller-supplied design must pass" — needs no separate assertion here:
    # `generate_ship` returns `build_ship(design)`, so a sweep that completes
    # without raising has already run every generated design through the
    # sole validation authority.
    for seed in range(2000):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert ship.cargo_tons >= 0
        assert ship.tonnage_used <= ship.hull_tons


# --- Phase 5, User Story 3: determinism, small craft and authored designs
# stay predictable.


def test_sc006_generation_is_deterministic_on_every_path():
    for seed in range(2000):
        assert generate_ship(RandomRolls.seeded(seed)) == generate_ship(RandomRolls.seeded(seed))
        assert generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT) == generate_ship(
            RandomRolls.seeded(seed), constraints=_SMALL_CRAFT
        )
        assert generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=400)
        ) == generate_ship(RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=400))


def test_sc005_small_craft_output_is_unchanged_from_before_the_change():
    with open(_PRE_CHANGE_SWEEP_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)["small_craft"]

    for seed_text, expected_toml in baseline.items():
        seed = int(seed_text)
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert dump_design(ship.design) == expected_toml


def test_sc009_hull_size_is_always_honored():
    for hull_tons in sorted(HULLS):
        for seed in range(10):
            ship = generate_ship(
                RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=hull_tons)
            ).ship
            assert ship.hull_tons == hull_tons


def test_sc008_ship_name_is_the_final_draw_and_is_drawn_exactly_once_on_both_paths():
    for seed in range(50):
        for hull_class in HullClass:
            recorder = RecordingRolls(RandomRolls.seeded(seed))
            generate_ship(recorder, constraints=DesignConstraints(hull_class=hull_class))
            assert _names(recorder)[-1] == RollName.SHIP_NAME
            assert _names(recorder).count(RollName.SHIP_NAME) == 1


def test_a_pinned_hull_tonnage_draws_no_dice_on_either_path():
    """Pinning spends an answer, not a roll.

    `RecordingRolls` is the only way to see this: the ship alone cannot say
    whether the hull was drawn and discarded or never drawn at all, and the
    difference is exactly what keeps the pinned baseline meaningful.
    """
    for seed in range(20):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(recorder, constraints=DesignConstraints(hull_tons=400))
        assert RollName.SHIP_HULL_SIZE not in _names(recorder)

        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(
            recorder,
            constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=40),
        )
        assert RollName.SHIP_HULL_SIZE not in _names(recorder)


def test_an_unpinned_hull_tonnage_is_drawn_exactly_once_on_either_path():
    """The other half: without a pin the draw is still made, so the test above
    cannot pass by the roll having been removed altogether."""
    for hull_class in HullClass:
        recorder = RecordingRolls(RandomRolls.seeded(3))
        generate_ship(recorder, constraints=DesignConstraints(hull_class=hull_class))
        assert _names(recorder).count(RollName.SHIP_HULL_SIZE) == 1


def test_sc008_drive_codes_are_drawn_jump_then_maneuver_then_power():
    for seed in range(50):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(recorder)
        jump_at = _names(recorder).index(RollName.SHIP_JUMP_CODE)
        maneuver_at = _names(recorder).index(RollName.SHIP_MANEUVER_CODE)
        power_at = _names(recorder).index(RollName.SHIP_POWER_CODE)
        assert jump_at < maneuver_at < power_at

    for seed in range(50):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(recorder, constraints=_SMALL_CRAFT)
        assert RollName.SHIP_JUMP_CODE not in _names(recorder)
        maneuver_at = _names(recorder).index(RollName.SHIP_MANEUVER_CODE)
        power_at = _names(recorder).index(RollName.SHIP_POWER_CODE)
        assert maneuver_at < power_at


def test_sc008_re_pinned_baseline_pins_seeded_designs_for_future_features():
    # A blunt regression net for *future* features, not this one — the data
    # was generated from this feature's own post-change generator.
    with open(_POST_CHANGE_BASELINE_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)

    for key, expected_toml in baseline.items():
        path, seed_text = key.split(":")
        seed = int(seed_text)
        ship = generate_ship(
            RandomRolls.seeded(seed),
            constraints=_SMALL_CRAFT if path == "small_craft" else UNCONSTRAINED,
        ).ship
        assert dump_design(ship.design) == expected_toml, f"{key}: moved off the pinned baseline"


# --- Phase 7 Convergence: pins for properties that already held but were
# asserted nowhere in the suite. Neither test drove a source change.


def _lightest_code_at(hull_tons: int, rating: int) -> str:
    return min(
        (code for code, ratings in DRIVE_PERFORMANCE.items() if ratings.get(hull_tons) == rating),
        key=lambda code: DRIVE_COSTS[code].jump_tons,
    )


def test_g4_every_generated_starship_mounts_the_lightest_drive_at_its_rating():
    """Contract G4.

    This is a standing rule applied to every generated starship, but nothing
    asserted it at the `generate_ship` level:
    `test_sc007_ships_already_fully_fueled_before_the_change_keep_their_rating`
    checks only that a *changed* letter is strictly lighter, and the C3 tests
    cover `_fit_jump_drive` rather than the wiring. Before this test, a
    regression reinstating a heavier same-rating drive passed `uv run pytest`
    and the pre-push gate, caught only by the manual survey script.
    """
    starved = 0
    for seed in range(2000):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        # G4 binds even on a starved-hull ship: the fallback defers to the same
        # rule for the choice among drives sharing the lowest rating, so this is
        # asserted before the starved-hull classification, not after it.
        assert ship.design.jump_code == _lightest_code_at(ship.hull_tons, ship.jump_rating)
        if _is_fr014_starved_hull_ship(ship):
            starved += 1
    assert starved == 0


def test_fr003_affordability_and_the_generators_fuel_arithmetic_agree_at_the_boundary():
    """A property to pin, not one to assume.

    `_fit_jump_drive` admits a rating when `jump_tons + 0.1 * hull * rating`
    fits the budget; `generate_ship` then decides how many jumps the leftover
    tonnage actually buys with `math.floor(remaining / (0.1 * hull))`. The two
    must agree at the tightest budget the first accepts, or the search could
    select a rating the allocation then refuses to fund. They do for every hull
    and rating in the current tables, but the agreement rests on floating-point
    behavior rather than on anything the SRD guarantees.
    """
    for hull_tons in HULLS:
        for code, ratings in DRIVE_PERFORMANCE.items():
            if hull_tons not in ratings:
                continue
            rating = ratings[hull_tons]
            jump_tons = DRIVE_COSTS[code].jump_tons
            budget = jump_tons + 0.1 * hull_tons * rating  # exactly affordable
            remaining = max(0.0, budget - jump_tons)
            assert math.floor(remaining / (0.1 * hull_tons)) >= rating


# --- Phase 8 Convergence: the starved-hull "must still validate" clause ---


def test_fr014_a_starved_hull_design_still_builds_within_its_hull():
    """The starved-hull "MUST still satisfy" build-validation clause and
    contract G5.

    For a starved hull the contract drops every guarantee but G4 and G5, and
    G5 — the design still fits — was asserted nowhere: the C5 and C6 tests
    check only which *letter* `_fit_jump_drive` returns, never that a design
    built around that letter fits its hull.

    A *genuinely* starved hull cannot be reached, and not merely through
    `generate_ship`: the fallback drive is the lowest-rated legal one, and on
    every tabulated hull the mandatory systems leave room to fuel it for a full
    jump (reconfirmed here — 0 of 18 hulls fall short). So
    there is no configuration of real tables under which a starved-hull fuel
    shortfall occurs, and a test that merely rebuilt the fallback allocation
    would quietly assert an ordinary fully-fueled ship.

    What is pinned instead is the *shape* the starved-hull clause permits: the
    fallback drive carrying "whatever fuel fits", swept across every jump
    distance from 0 (the degenerate zero-jump ship the clause explicitly
    allows) up to its full rating. Every one of those designs must build and
    fit inside its hull.
    """
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        top = max(legal, key=lambda code: DRIVE_PERFORMANCE[code][hull_tons])
        fallback = _fit_jump_drive(hull_tons, top, 0.0)
        rating = DRIVE_PERFORMANCE[fallback][hull_tons]

        # The heaviest power plant the drive's rating floor admits, so the
        # mandatory systems take as much of the hull as the rules allow.
        maneuver = min(legal, key=lambda code: DRIVE_COSTS[code].maneuver_tons)
        required = max(rating, DRIVE_PERFORMANCE[maneuver][hull_tons])
        power = max(
            (code for code in legal if DRIVE_PERFORMANCE[code][hull_tons] >= required),
            key=lambda code: DRIVE_COSTS[code].power_tons,
        )

        for distance in range(0, rating + 1):
            ship = build_ship(
                ShipDesign(
                    hull_tons=hull_tons,
                    jump_code=fallback,
                    maneuver_code=maneuver,
                    power_code=power,
                    jump_distance=distance,
                    power_weeks=2,
                )
            )

            assert ship.tonnage_used <= ship.hull_tons  # G5
            assert ship.cargo_tons >= 0
            assert ship.assumed_jump_distance == distance  # never silently corrected
            assert ship.jump_fuel == pytest.approx(0.1 * hull_tons * distance)


# --- what may be offered for a drive, as narrow as what is known allows ---


def test_offerable_ratings_narrows_a_small_craft_maneuver_once_the_hull_is_known():
    """The drive table tabulates ratings a 40-ton hull could reach in isolation;
    a craft also needs a plant and a cockpit. The narrower answer is the true one
    and is what both the prompt and generation have to work from."""
    tabulated = available_ratings(HullClass.SMALL_CRAFT, 40)
    offerable = offerable_ratings(HullClass.SMALL_CRAFT, 40, Drive.MANEUVER)
    assert offerable == small_craft_maneuver_ratings(40)
    assert set(offerable) < set(tabulated), "the small-craft path should narrow"


def test_offerable_ratings_cannot_narrow_before_the_hull_is_known():
    """With the tonnage left to the dice there is nothing to narrow against, so
    the tabulated answer stands rather than a guess at one."""
    for drive in Drive:
        assert offerable_ratings(HullClass.SMALL_CRAFT, None, drive) == available_ratings(
            HullClass.SMALL_CRAFT, None
        )


def test_offerable_ratings_narrows_a_small_craft_plant_only_once_its_drive_is_pinned():
    """The pair is chosen jointly on this path: a maneuver drive still left to
    the dice rules nothing out, but one already pinned rules out plants too weak
    to power it or too heavy to sit beside it."""
    unpinned = offerable_ratings(HullClass.SMALL_CRAFT, 15, Drive.POWER)
    assert unpinned == available_ratings(HullClass.SMALL_CRAFT, 15)

    pinned = offerable_ratings(HullClass.SMALL_CRAFT, 15, Drive.POWER, 1)
    assert pinned == small_craft_power_ratings(15, 1)
    assert set(pinned) <= set(unpinned)


@pytest.mark.parametrize("drive", list(Drive), ids=[drive.value for drive in Drive])
def test_offerable_ratings_never_widens_past_what_the_tables_tabulate(drive):
    """Narrowing may only ever remove. A rating offered but not tabulated would
    promise the referee something no drive can deliver."""
    for hull_class, tonnages in (
        (HullClass.STARSHIP, sorted(HULLS)),
        (HullClass.SMALL_CRAFT, sorted(SMALL_CRAFT_HULLS)),
    ):
        for hull_tons in (None, *tonnages):
            tabulated = set(available_ratings(hull_class, hull_tons))
            for maneuver_rating in (None, *range(1, 7)):
                offerable = offerable_ratings(hull_class, hull_tons, drive, maneuver_rating)
                assert set(offerable) <= tabulated, (hull_class, hull_tons, maneuver_rating)


# --- the dice never cost the referee a ship over an answer they never gave ---


_RESTRICTED_FITTINGS = tuple(
    kind for kind, row in FITTINGS.items() if row.forbidden_on_distributed
)


def _honored_or_declared(result, field: str, honored: bool) -> bool:
    """The protocol in one line: the pin is honored, or its absence is declared.

    Generation is allowed to fall short of a pin the hull cannot pay for—that is
    what `unmet` is for—but it is never allowed to fall short silently, and never
    allowed to refuse the ship outright.
    """
    return honored or any(entry.field == field for entry in result.unmet)


@pytest.mark.parametrize("kind", _RESTRICTED_FITTINGS)
@pytest.mark.parametrize(
    "hull_class", [HullClass.STARSHIP, HullClass.SMALL_CRAFT], ids=["starship", "small_craft"]
)
def test_a_pinned_fitting_survives_a_rolled_configuration(hull_class, kind):
    """A fitting the referee pinned is not lost to a configuration they left to chance.

    `fuel_scoops` cannot go on a distributed hull. The configuration was rolled,
    not asked for, so before this the dice could pick distributed and `build_ship`
    would refuse the design—costing the session a ship over an answer the referee
    never gave. The draw now skips the configurations that would forbid the pin.
    """
    constraints = DesignConstraints(hull_class=hull_class, fittings=(FittingFit(kind=kind),))
    for seed in range(150):
        result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)
        fitted = any(fit.kind == kind for fit in result.ship.design.fittings)
        assert _honored_or_declared(result, "fittings", fitted), seed


@pytest.mark.parametrize("rating", available_ratings(HullClass.STARSHIP, None))
def test_a_pinned_jump_rating_survives_a_rolled_hull(rating):
    """A rating the referee pinned is not lost to a hull they left to chance.

    Not every tonnage tabulates every rating, so drawing from all of them let the
    dice pick a hull the pin could not be delivered on. The hull is now drawn from
    the tonnages that can deliver it.
    """
    constraints = DesignConstraints(jump_rating=rating)
    for seed in range(60):
        result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)
        assert _honored_or_declared(result, "jump_rating", result.ship.jump_rating == rating), seed


@pytest.mark.parametrize("drive", ["maneuver_rating", "power_rating"])
@pytest.mark.parametrize("rating", available_ratings(HullClass.SMALL_CRAFT, None))
def test_a_pinned_small_craft_rating_survives_a_rolled_hull(rating, drive):
    """The small-craft path narrows its hull draw by the same rule.

    Small hulls tabulate ratings just as unevenly as large ones, so this path had
    the same defect and needed the same fix; only the table it draws from differs.
    """
    constraints = DesignConstraints(hull_class=HullClass.SMALL_CRAFT, **{drive: rating})
    for seed in range(60):
        result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)
        delivered = getattr(result.ship, drive.removesuffix("_rating") + "_rating")
        assert _honored_or_declared(result, drive, delivered == rating), seed


def test_a_pin_no_hull_can_honor_does_not_take_the_other_pins_down_with_it():
    """Narrowing is per pin, so an impossible one costs only its own filter.

    Two turrets fit no small craft, and narrowing on all the pins at once emptied
    the pool and fell back to every hull—dropping the *rating* narrowing too. The
    dice then drew a hull the pinned rating was not tabulated for, and the refusal
    blamed the rating, which the referee could have had, instead of the turret
    count, which they could not.
    """
    constraints = DesignConstraints(
        hull_class=HullClass.SMALL_CRAFT, power_rating=3, turrets=(TurretPin(),) * 3
    )
    for seed in range(60):
        with pytest.raises(ValueError, match="hardpoint") as refusal:
            generate_ship(RandomRolls.seeded(seed), constraints=constraints)
        assert "power rating" not in str(refusal.value), seed


def test_a_pin_no_hull_of_the_class_can_honor_is_still_refused():
    """Narrowing cannot invent a hull. A small craft has one hardpoint however
    large it is, so a second pinned turret is refused on every hull rather than
    unluckily on this one—an empty pool is a different answer from a bad roll,
    and belongs to the validator that can say which."""
    for seed in range(20):
        with pytest.raises(ValueError, match="hardpoint"):
            generate_ship(
                RandomRolls.seeded(seed),
                constraints=DesignConstraints(
                    hull_class=HullClass.SMALL_CRAFT, turrets=(TurretPin(),) * 2
                ),
            )


@pytest.mark.parametrize("count", [1, 2, 3, 5])
def test_a_pinned_turret_count_survives_a_rolled_hull(count):
    """Hardpoints come from tonnage, so a turret count pins the hull it needs."""
    constraints = DesignConstraints(turrets=(TurretPin(),) * count)
    for seed in range(60):
        result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)
        met = len(result.ship.design.turrets) == count
        assert _honored_or_declared(result, "turrets", met), seed


# Narrowing the pool must never empty it, or the dice would have nothing to draw
# from and the fix would trade one refusal for another.
@pytest.mark.parametrize("rating", available_ratings(HullClass.STARSHIP, None))
def test_every_tabulated_rating_leaves_the_dice_a_hull_to_draw(rating):
    honoring = [
        tons for tons in sorted(HULLS) if rating in available_ratings(HullClass.STARSHIP, tons)
    ]
    assert honoring, f"rating {rating} is tabulated for no hull at all"


def test_every_reachable_turret_count_leaves_the_dice_a_hull_to_draw():
    most = max(hardpoints(HullClass.STARSHIP, tons) for tons in sorted(HULLS))
    for count in range(1, most + 1):
        honoring = [
            tons for tons in sorted(HULLS) if hardpoints(HullClass.STARSHIP, tons) >= count
        ]
        assert honoring, f"{count} turrets fit no hull at all"


# --- but two pins that contradict each other are still the referee's mistake ---


_CONTRADICTORY_PINS = [
    (
        "hull too small for the turret count",
        DesignConstraints(hull_tons=100, turrets=(TurretPin(),) * 3),
        "hardpoint",
    ),
    (
        "hull does not tabulate the rating",
        DesignConstraints(hull_tons=4000, jump_rating=3),
        "not tabulated",
    ),
    (
        "configuration forbids the fitting",
        DesignConstraints(
            configuration=Configuration.DISTRIBUTED, fittings=(FittingFit(kind="fuel_scoops"),)
        ),
        "distributed hull cannot mount",
    ),
    (
        "plant rated below the drive it powers",
        DesignConstraints(hull_tons=400, jump_rating=4, power_rating=1),
        "below required",
    ),
]


@pytest.mark.parametrize(
    "label, constraints, message", _CONTRADICTORY_PINS, ids=[c[0] for c in _CONTRADICTORY_PINS]
)
def test_two_pins_that_contradict_each_other_still_refuse(label, constraints, message):
    """Narrowing applies to the dice, never to the referee.

    A roll is only a preference and yields to a pin, but a pin is a promise and
    two promises that cannot both be kept are a mistake worth a sentence rather
    than a ship that quietly honors whichever was easier.
    """
    with pytest.raises(ValueError, match=message):
        generate_ship(RandomRolls.seeded(3), constraints=constraints)


# --- the tonnage ledger agrees with the builder's allocation ---


def _assert_ledger_matches_cargo(monkeypatch, constraints, seeds):
    """Every generation's final `remaining` equals the ship's `cargo_tons`.

    `generate_ship` decides what a hull can afford against a ledger it keeps to
    itself, then hands the design to `build_ship`, which allocates the tonnage
    for real. The two arithmetics are written out separately—bridge, armor,
    small-craft fuel, power fuel, jump fuel, hardpoints, fittings and bays are
    each spelled once in `generator.py` and once in `builder.py`—and nothing
    compared them. `cargo_tons >= 0`, asserted in several tests above, is far
    too weak: a ledger that under-counts still satisfies it and merely stops
    fitting components the hull could hold, silently.

    The ledger is not on `GenerationResult`, so the only way to read it is to
    watch it being built. The probe subclasses the real ledger rather than
    faking one, so what is asserted is the arithmetic generation actually ran.
    """
    captured: list[TonnageLedger] = []

    class _ProbedLedger(TonnageLedger):
        def __init__(self, tons: float) -> None:
            super().__init__(tons)
            captured.append(self)

    monkeypatch.setattr("cetools.engine.ships.generator.TonnageLedger", _ProbedLedger)

    for seed in range(seeds):
        captured.clear()
        result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)

        assert len(captured) == 1, f"seed {seed}: expected one ledger, got {len(captured)}"
        # Approximate, and the tolerance is doing real work. The starship path
        # agrees to the bit; the small-craft path does not, because its power
        # fuel is `math.floor(power_tons / 3 * 10) / 10`—tenths like 5.3, which
        # no binary float holds exactly. The ledger subtracts them one component
        # at a time while the builder sums and subtracts once, so the two land up
        # to 4e-15 apart on about one seed in six. Real drift is at least 0.1t,
        # the granularity every tonnage formula rounds to, so 1e-9 sits far above
        # the noise and far below anything worth catching.
        assert captured[0].remaining == pytest.approx(result.ship.cargo_tons, abs=1e-9), (
            f"seed {seed}: ledger left {captured[0].remaining}t, "
            f"builder left {result.ship.cargo_tons}t"
        )


@pytest.mark.parametrize(
    "hull_class",
    [HullClass.STARSHIP, HullClass.SMALL_CRAFT],
    ids=["starship", "small_craft"],
)
def test_the_ledger_matches_the_builder_across_seeds(monkeypatch, hull_class):
    _assert_ledger_matches_cargo(monkeypatch, DesignConstraints(hull_class=hull_class), seeds=200)


# Pinned shapes the dice reach rarely or never: the tonnage extremes, the
# dearest armor, more staterooms than most hulls can hold, and one of each
# component that is drawn against the budget. `jump_rating` is deliberately
# absent—pinning it escapes as a ValueError on some seeds, which is a separate
# defect, and folding it in here would make that regression and a ledger drift
# fail the same test.
_LEDGER_PINS = [
    ("hull_tons=100", DesignConstraints(hull_tons=100)),
    ("hull_tons=2000", DesignConstraints(hull_tons=2000)),
    (
        "armor=crystaliron_10",
        DesignConstraints(armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=10),)),
    ),
    ("staterooms=20", DesignConstraints(staterooms=20)),
    ("fitting=laboratory", DesignConstraints(fittings=(FittingFit(kind="laboratory"),))),
    ("bay=meson", DesignConstraints(bays=(BayFit(kind="meson"),))),
    ("screen=nuclear_damper", DesignConstraints(screens=(ScreenFit(kind="nuclear_damper"),))),
    (
        "small_craft hull_tons=40",
        DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=40),
    ),
    (
        "small_craft staterooms=2",
        DesignConstraints(hull_class=HullClass.SMALL_CRAFT, staterooms=2),
    ),
]


@pytest.mark.parametrize(
    "label, constraints", _LEDGER_PINS, ids=[label for label, _ in _LEDGER_PINS]
)
def test_the_ledger_matches_the_builder_when_a_field_is_pinned(monkeypatch, label, constraints):
    _assert_ledger_matches_cargo(monkeypatch, constraints, seeds=100)


# --- a single build or generation is effectively instant ---


def test_a_single_build_completes_in_under_a_tenth_of_a_second():
    design = load_design("tests/data/ships/free-trader.toml")
    build_ship(design)  # warm up imports before timing

    start = time.perf_counter()
    build_ship(design)
    assert time.perf_counter() - start < 0.1


def test_a_single_generation_completes_in_under_a_tenth_of_a_second():
    generate_ship(RandomRolls.seeded(1))  # warm up imports before timing

    start = time.perf_counter()
    generate_ship(RandomRolls.seeded(2))
    assert time.perf_counter() - start < 0.1
