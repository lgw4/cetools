"""render_description(ship) -> the ship's Universal Ship Description Format text.

A heading line, a blank line, and one unwrapped paragraph, exactly as the SRD's
worked ship examples set it out. A pure function of the `Ship` alone:
it reads no clock, no seed, no environment and no locale, and every grouping
walks an ordered tuple in first-appearance order, so two equal ships render
byte-identically.

The paragraph is assembled from `_SLOTS`, a fixed sixteen-entry tuple of
sentence builders in a fixed order. Each returns `str | None`, and `None`
drops that slot from the paragraph entirely. Omission is the only
control flow between slots -- no builder reads another's output -- so the
paragraph stays grammatical however many drop out. `_weapons` is the sole
builder whose return value carries more than one sentence: its ammunition
sentences ride along with the installed-weapons sentence, so a paragraph has
sixteen *slots* but can run past sixteen sentences.

Imports only `models`, `tables` and `prose`: every SRD spelling, plural and
tech level comes from a table column rather than from a branch keyed on a
component's name.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

from cetools.engine.ships.models import HullClass, Ship
from cetools.engine.ships.prose import (
    article,
    count,
    join,
    money,
    number,
    plural,
    signed,
    tonnage_article,
    tons,
)
from cetools.engine.ships.tables import (
    AMMO,
    ARMOR,
    ARMOR_OPTIONS,
    BAYS,
    CONFIGURATIONS,
    CREW_POSITIONS,
    ELECTRONICS,
    FITTINGS,
    SCREENS,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)

_UNNAMED = "Unnamed Ship"
"""The heading and first sentence's stand-in for a design with no name."""

_DEFAULT_ELECTRONICS = "standard"
"""Every ship carries the Standard suite included in its bridge or cockpit, so
the sensors sentence is never omitted."""

_ARTICLES = ("a ", "an ")
"""`FittingRow.name` carries its indefinite article; the hangar sentence counts
its noun ("one small craft hangar") and so needs the bare form."""


def _ship_name(ship: Ship) -> str:
    # A blank name is no name: `loads_design` accepts `name = ""`, and
    # the heading's `TL<n> <name>` shape has no room for a name that is not there.
    name = ship.design.name
    return name if name is not None and name.strip() else _UNNAMED


def _is_small_craft(ship: Ship) -> bool:
    return ship.design.hull_class is HullClass.SMALL_CRAFT


def _bare(name: str) -> str:
    """A display name without the indefinite article its column carries."""
    for prefix in _ARTICLES:
        if name.startswith(prefix):
            return name.removeprefix(prefix)
    return name


def _grouped(items: Iterable, key: Callable) -> list[tuple]:
    """`(key, count)` pairs in first-appearance order over `items`.

    First-appearance order over the design's ordered tuples—never a `set` or a
    dict keyed on unordered input—is what makes the paragraph byte-identical
    for equal ships.
    """
    order: list = []
    counts: dict = {}
    for item in items:
        group = key(item)
        if group not in counts:
            order.append(group)
            counts[group] = 0
        counts[group] += 1
    return [(group, counts[group]) for group in order]


def _ammo_row(kind: str, type_: str | None):
    """The `AMMO` row for one `AmmoFit`, matched on the row's ``kind``/``type``
    columns rather than on a key spelling. `AmmoFit`'s own validation
    guarantees a match."""
    return next(row for row in AMMO.values() if row.kind == kind and row.type == type_)


# --- 1. Hull and purpose ---------------


def _hull(ship: Ship) -> str:
    design = ship.design
    purpose = design.purpose
    if purpose is None:
        purpose = "a small craft" if _is_small_craft(ship) else "a starship"
    return (
        f"Using {tonnage_article(ship.hull_tons)} {number(ship.hull_tons)}-ton hull "
        f"({number(ship.hull_points)} Hull, {number(ship.structure_points)} Structure), "
        f"the {_ship_name(ship)} is {purpose}."
    )


# --- 2. Drives and performance ------------------


def _drives(ship: Ship) -> str:
    design = ship.design
    starship = not _is_small_craft(ship)

    drives = []
    if starship and design.jump_code is not None:
        drives.append(f"jump drive {design.jump_code}")
    if design.maneuver_code is not None:
        drives.append(f"maneuver drive {design.maneuver_code}")
    drives.append(f"power plant {design.power_code}")

    performance = []
    if starship:
        performance.append(f"Jump-{number(ship.jump_rating)}")
    if design.maneuver_code is not None:
        performance.append(f"{number(ship.maneuver_rating)}-G acceleration")

    text = f"It mounts {join(drives)}"
    if performance:
        text += f", giving a performance of {join(performance)}"
    return f"{text}."


# --- 3. Fuel and endurance ----------------------


def _fuel(ship: Ship) -> str:
    weeks = ship.design.power_weeks
    tankage = ship.jump_fuel + ship.power_fuel
    text = (
        f"Fuel tankage of {tons(tankage)} {plural(tankage, 'ton', 'tons')} supports "
        f"the power plant for {count(weeks)} {plural(weeks, 'week', 'weeks')}"
    )
    if _is_small_craft(ship):
        return f"{text}."
    # The jumps the tankage supports at the rated distance. Kept even at zero,
    # which is what a design buying no jump fuel states.
    jumps = ship.assumed_jump_distance // ship.jump_rating if ship.jump_rating else 0
    return (
        f"{text} and {count(jumps)} Jump-{number(ship.jump_rating)} "
        f"{plural(jumps, 'jump', 'jumps')}."
    )


# --- 4. Computer -----------------------------------------


def _computer(ship: Ship) -> str | None:
    fit = ship.design.computer
    if fit is None:
        return None
    suffix = ""
    if fit.jump_control:
        suffix += "/bis"
    if fit.hardened:
        suffix += "/fib"
    station = "cockpit" if _is_small_craft(ship) else "bridge"
    return f"Adjacent to the {station} is a computer Model {number(fit.model)}{suffix}."


# --- 5. Sensors --------------------------------


def _sensors(ship: Ship) -> str:
    row = ELECTRONICS[ship.design.electronics or _DEFAULT_ELECTRONICS]
    return f"The ship is equipped with {row.name} sensors (DM{signed(row.dm)})."


# --- 6. Quarters --------------------------------

_QUARTERS = (
    ("staterooms", "stateroom", "staterooms"),
    ("low_berths", "low berth", "low berths"),
    ("emergency_low_berths", "emergency low berth", "emergency low berths"),
)


def _quarters(ship: Ship) -> str | None:
    clauses = []
    last = 0
    for field_name, singular, many in _QUARTERS:
        berths = getattr(ship.design, field_name)
        if berths <= 0:
            continue
        clauses.append(f"{count(berths)} {plural(berths, singular, many)}")
        last = berths
    if not clauses:
        return None
    verb = "is" if len(clauses) == 1 and last == 1 else "are"
    return f"There {verb} {join(clauses)}."


# --- 7. Hardpoints and fire control ---------------------


def _hardpoints(ship: Ship) -> str:
    # The SRD's Chapter 9 examples all report fire-control tonnage as the
    # hardpoint count; no computed value changes.
    points = ship.hardpoints
    text = (
        f"The ship has {count(points)} {plural(points, 'hardpoint', 'hardpoints')} and "
        f"{tons(points)} {plural(points, 'ton', 'tons')} allocated to fire control"
    )
    if ship.hardpoints_used == 0:
        text += ", but has no weapons installed"
    return f"{text}."


# --- 8. Installed weapons and ammunition ----------------


def _turret_armament(weapons: Sequence[str]) -> str:
    """A turret's weapon phrases, its slots grouped by weapon in slot order: a
    weapon filling one slot names itself ("a pulse laser"), one filling more
    renders its plural with no count ("missiles")."""
    phrases = []
    for weapon, slots in _grouped(weapons, lambda name: name):
        row = TURRET_WEAPONS[weapon]
        phrases.append(f"{article(row.name)} {row.name}" if slots == 1 else row.plural)
    return join(phrases)


def _opens_a_sentence(text: str) -> str:
    """`text` with its first character capitalised.

    The ammunition sentence is the one slot whose first word is a count, and
    counts of ten or fewer are spelled as a word -- so "three smart missiles
    ..." needs the capital every other sentence gets from a fixed opening word.
    `str.capitalize` is wrong here: it lower-cases the rest, which would ruin a
    display name.
    """
    return text[:1].upper() + text[1:]


def _ammunition(design) -> list[str]:
    """One sentence per `(kind, type)` group, aggregated across every turret in
    first-appearance order and naming its weapon through `AmmoRow.weapon`."""
    order: list = []
    rounds: dict = {}
    for turret in design.turrets:
        for ammo in turret.ammo:
            group = (ammo.kind, ammo.type)
            if group not in rounds:
                order.append(group)
                rounds[group] = 0
            rounds[group] += ammo.count

    sentences = []
    for group in order:
        row = _ammo_row(*group)
        weapon = TURRET_WEAPONS[row.weapon]
        loaded = rounds[group]
        turrets = sum(1 for turret in design.turrets if row.weapon in turret.weapons)
        sentences.append(
            _opens_a_sentence(
                f"{count(loaded)} {plural(loaded, row.name, row.plural)} "
                f"{plural(loaded, 'is', 'are')} carried as ammunition for the {weapon.name} "
                f"{plural(turrets, 'turret', 'turrets')}."
            )
        )
    return sentences


def _weapons(ship: Ship) -> str | None:
    design = ship.design
    if not design.turrets and not design.bays:
        return None

    # Bays before turrets, each group in first-appearance order.
    groups = []
    for kind, fitted in _grouped(design.bays, lambda bay: bay.kind):
        row = BAYS[kind]
        groups.append(f"{count(fitted)} {plural(fitted, row.name, row.plural)}")
    for (mount, weapons), fitted in _grouped(
        design.turrets, lambda turret: (turret.mount, turret.weapons)
    ):
        row = TURRET_MOUNTS[mount]
        groups.append(
            f"{count(fitted)} {plural(fitted, row.name, row.plural)} "
            f"armed with {_turret_armament(weapons)}"
        )

    systems = len(design.bays) + len(design.turrets)
    sentence = (
        f"Installed on the {plural(systems, 'hardpoint', 'hardpoints')} "
        f"{plural(systems, 'is', 'are')} {join(groups)}."
    )
    return " ".join([sentence, *_ammunition(design)])


# --- 9. Screens --------------------------------------------------


def _screens(ship: Ship) -> str | None:
    screens = ship.design.screens
    if not screens:
        return None
    groups = []
    for kind, fitted in _grouped(screens, lambda screen: screen.kind):
        row = SCREENS[kind]
        if fitted == 1:
            groups.append(f"{article(row.name)} {row.name}")
        else:
            groups.append(f"{count(fitted)} {row.plural}")
    total = len(screens)
    return f"This ship has {count(total)} {plural(total, 'screen', 'screens')}: {join(groups)}."


# --- 10. Small craft hangars -----------------------------


def _hangar_fittings(design) -> list:
    """Every vehicle-sized fitting, identified by its row's per-vehicle-ton
    column and never by a key comparison."""
    return [fit for fit in design.fittings if FITTINGS[fit.kind].tons_per_vehicle_ton is not None]


def _capacity(vehicle_tons: float) -> str:
    return f"{tons(vehicle_tons)} {plural(vehicle_tons, 'ton', 'tons')} of small craft"


def _hangar_phrase(kind: str, fittings: Sequence) -> str:
    """One kind of hangar: its count, its own row's noun, and its capacities.

    The noun comes from this kind's row and never from another's, so a design
    fitting two vehicle-sized rows names each of them correctly.
    """
    row = FITTINGS[kind]
    fitted = sum(fit.quantity for fit in fittings)
    noun = f"{count(fitted)} {plural(fitted, _bare(row.name), row.plural)}"
    if len(fittings) == 1:
        each = "" if fitted == 1 else ", each"
        return f"{noun}{each} holding {_capacity(fittings[0].vehicle_tons)}"
    clauses = [f"{count(fit.quantity)} holding {_capacity(fit.vehicle_tons)}" for fit in fittings]
    return f"{noun}, {join(clauses)}"


def _hangars(ship: Ship) -> str | None:
    fittings = _hangar_fittings(ship.design)
    if not fittings:
        return None

    by_kind: dict[str, list] = {}
    for fit in fittings:
        by_kind.setdefault(fit.kind, []).append(fit)
    phrases = [_hangar_phrase(kind, entries) for kind, entries in by_kind.items()]

    # Proximity agreement: the verb follows the first phrase's count, which for
    # a single kind -- every SRD design today -- is the ship's whole hangar count.
    leading = sum(fit.quantity for fit in next(iter(by_kind.values())))
    return f"There {plural(leading, 'is', 'are')} {join(phrases)}."


# --- 11. Cargo ---------------------------------------------------


def _cargo(ship: Ship) -> str:
    capacity = ship.cargo_tons
    return f"Cargo capacity is {tons(capacity)} {plural(capacity, 'ton', 'tons')}."


# --- 12. Hull configuration and armor ---------


def _distinct(names: Iterable[str]) -> list[str]:
    """`names` deduplicated, in first-appearance order."""
    seen: list[str] = []
    for name in names:
        if name not in seen:
            seen.append(name)
    return seen


def _configuration(ship: Ship) -> str:
    hull = CONFIGURATIONS[ship.configuration.value].name
    layers = ship.design.armor
    if not layers:
        return f"The hull is {hull}, and no additional armor has been installed."

    # Two layers yield one armor clause and one total protection rating.
    types = _distinct(ARMOR[fit.type.value].name for fit in layers)
    # Read from the ship, not from its layers: a coating is on the hull, so it
    # is named once however many layers are under it.
    options = _distinct(ARMOR_OPTIONS[opt].name for opt in ship.design.armor_options)
    armored = f"{join(types)} ({number(ship.armor_protection)} points)"
    if options:
        return f"The hull is {hull}, armored with {armored}, and possesses {join(options)}."
    return f"The hull is {hull}, and is armored with {armored}."


# --- 13. Special features ----------------------------------------


def _feature(fit) -> str:
    """One fitting's clause, driven by the row's ``counted_in_tons`` and
    ``unrefined_fuel_per_ton`` columns rather than by its key."""
    row = FITTINGS[fit.kind]
    quantity = fit.quantity
    if row.counted_in_tons:
        clause = f"{tons(quantity)} {plural(quantity, 'ton', 'tons')} of {row.plural}"
        if row.unrefined_fuel_per_ton is not None:
            processed = quantity * row.unrefined_fuel_per_ton
            clause += (
                f" (processes {tons(processed)} tons of unrefined fuel "
                "into refined fuel per day)"
            )
        return clause
    if quantity == 1:
        return row.name
    return f"{count(quantity)} {row.plural}"


def _special_features(ship: Ship) -> str | None:
    # Hangars are rendered by sentence 10 and excluded here. So is anything the
    # hull shape already carries: a streamlined ship's scoops are part of its
    # streamlining, so naming them among its *additional* components would say
    # the ship has two sets. The builder drops the charge for the same entry.
    clauses = [
        _feature(fit)
        for fit in ship.design.fittings
        if FITTINGS[fit.kind].tons_per_vehicle_ton is None
        and not ship.design.configuration.includes(fit.kind)
    ]
    if not clauses:
        return None
    return f"Special features include {join(clauses)}."


# --- 14. Crew ----------------------------------------------------


def _crew(ship: Ship) -> str:
    clauses = []
    for position in CREW_POSITIONS:
        crewed = getattr(ship.crew, position.field)
        if crewed <= 0:
            continue
        clauses.append(f"{count(crewed)} {plural(crewed, position.name, position.plural)}")
    total = ship.crew.total
    return f"The ship requires a crew of {count(total)}: {join(clauses)}."


# --- 15. Passengers ----------------------------


def _passengers(ship: Ship) -> str:
    design = ship.design
    # Emergency low berths are survival equipment, not passenger capacity.
    spare = max(0, design.staterooms - ship.crew.total) * 2
    clauses = []
    if spare:
        clauses.append(
            f"{count(spare)} additional {plural(spare, 'passenger', 'passengers')} "
            "at double occupancy"
        )
    if design.low_berths:
        low = design.low_berths
        clauses.append(f"{count(low)} low {plural(low, 'passenger', 'passengers')}")
    if not clauses:
        return "The ship cannot carry any additional passengers."
    return f"The ship can carry up to {join(clauses)}."


# --- 16. Cost and build time -----------------------------


def _cost(ship: Ship) -> str:
    weeks = ship.build_weeks
    return (
        f"The ship costs MCr{money(ship.total_cost)} (including discounts and fees) "
        f"and takes {count(weeks)} {plural(weeks, 'week', 'weeks')} to build."
    )


_SLOTS: tuple[Callable[[Ship], str | None], ...] = (
    _hull,
    _drives,
    _fuel,
    _computer,
    _sensors,
    _quarters,
    _hardpoints,
    _weapons,
    _screens,
    _hangars,
    _cargo,
    _configuration,
    _special_features,
    _crew,
    _passengers,
    _cost,
)
"""The sixteen sentence slots, in a fixed order. The order lives here, as one
literal tuple, and nowhere else."""


def render_description(ship: Ship) -> str:
    """The ship's USDF heading and paragraph. Total: raises for no `Ship` that
    `build_ship` can return."""
    heading = f"TL{number(ship.tech_level)} {_ship_name(ship)}"
    sentences = [slot(ship) for slot in _SLOTS]
    return f"{heading}\n\n" + " ".join(text for text in sentences if text is not None)
