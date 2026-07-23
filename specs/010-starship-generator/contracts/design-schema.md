# Contract: TOML Design-File Schema

The structured design a caller feeds to `cetools ship build`, and the format `--toml` emits. Parsed
with stdlib `tomllib` into a `ShipDesign` (`load_design`); emitted by the in-repo writer
(`dump_design`). The schema is expressive enough to represent any ship the builder or random
generator can produce (FR-023), so any built or generated ship round-trips losslessly (SC-008).

## Top-level keys

```toml
name = "Beowulf"          # optional ship name (str)
hull_tons = 200           # required; a tabulated hull size
configuration = "streamlined"   # "distributed" | "standard" | "streamlined" (default "standard")
standard_design = false   # true applies the 10% common-design discount

[drives]
jump = "A"                # drive code letter; required for starships, omit for small craft
maneuver = "A"            # drive code letter; optional
power = "A"               # drive code letter; required for any powered craft
jump_distance = 1         # optional; intended jump range for fuel (default: full jump rating)
power_weeks = 2           # optional; >= 2 (starship) or >= 1 (small craft)

[bridge]
present = true            # starships; omit / false for small craft
cockpit = "1_man"         # small craft only: "1_man" | "2_man" | "1_man_cabin" | "2_man_cabin"

[computer]
model = 1                 # 1..7
jump_control = false
hardened = false
software = [              # each entry: name + rating level
  { name = "fire_control", level = 1 },
]

electronics = "basic_civilian"   # optional package name

[quarters]
staterooms = 2
low_berths = 0
emergency_low_berths = 0

[[armor]]                 # zero or more layers
type = "titanium_steel"   # "titanium_steel" | "crystaliron" | "bonded_superdense"
percent = 10              # multiple of 5
options = ["reflec"]      # subset of "reflec" | "self_sealing" | "stealth"

[[fittings]]              # zero or more
kind = "fuel_processor"
quantity = 1
# vehicle_tons = 13       # only for kind = "vehicle_hangar"

[[turrets]]               # zero or more
mount = "double"          # "single" | "double" | "triple" | "pop_up" | "fixed"
weapons = ["pulse_laser", "sandcaster"]
ammo = [                  # optional
  { kind = "sand_barrels", count = 20 },
  { kind = "missile", type = "standard", count = 12 },
]

[[bays]]                  # zero or more (starship only)
kind = "particle"         # "missile_bank" | "particle" | "meson" | "fusion"

[[screens]]               # zero or more
kind = "meson_screen"     # "meson_screen" | "nuclear_damper"

[passengers]
high = 0
middle = 0
```

## Rules enforced at load

`load_design` raises `ValueError` for: a missing/unknown `hull_tons`; an unknown enum string
(`configuration`, armor `type`, turret `mount`, bay/screen/fitting `kind`); a wrong value type; an
unknown top-level or section key; a small-craft hull carrying `[drives].jump` or a `[[bays]]` entry;
a starship missing `[drives].jump` or `[drives].power`; a bridge-and-cockpit conflict. Deeper
interaction checks (tonnage budget, power-plant rating, hardpoints, software rating) are the builder's
job and surface when `build_ship` runs.

## Emission (`dump_design`)

`dump_design` writes keys in the canonical order above, omitting sections that are empty/default so
the output stays minimal and stable. Enum values are written as their lowercase string forms. The
writer covers exactly the types above (str, int, float, bool, list of tables), which is all the
schema uses—no general TOML writer is needed.
