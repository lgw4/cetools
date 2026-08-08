# Contract: the vehicle design file

**Feature**: `001-vehicle-design` | **Date**: 2026-08-07

TOML, read by `loads_design` / `load_design` and written by `dump_design`, with
`loads_design(dump_design(d)) == d` for any well-formed design. Parsing validates **shape only**:
malformed TOML, unknown keys, wrong types and unknown enum strings raise `ValueError`. A
well-formed but illegal design loads cleanly and is rejected by `build_vehicle`. That split is
ships' and it is what lets the builder be the single authority on the rules.

## Shape

```toml
tech_level = 9              # required; a design without one fails to build
chassis = "F"               # required; a chassis code
configuration = "closed"    # or "open"; defaults to closed
configuration_options = ["streamlined"]
armor_options = ["reflec"]
standard_design = true      # elects the 10% discount
fuel_weeks = 4.0
controls = "advanced"
drone_controller = "advanced"
robot_brain = "basic"
communications = "class-ii"
communicator_type = "laser"
sensors = "standard"
life_support = "basic"
crew = 1
trailer = "medium"

[power_plant]
code = "D"
kind = "fusion"

[propulsion]
code = "F"
kind = "grav"

[propulsion_options]
kinds = ["off-road"]

[computer]
model = 1
hardened = false

[[armor]]
type = "bonded-superdense"
increments = 2

[[accommodations]]
kind = "seat-adequate"
count = 4

[[components]]
kind = "airlock"
count = 1

[[mounts]]
kind = "turret"
mount = "single-turret"

  [[mounts.weapons]]
  name = "machinegun-tl5"

    [[mounts.weapons.ammunition]]
    spaces = 0.5
```

## Rules

**`tech_level` is the only field with no default and no derivation.** FR-011 makes it required, and
`build_vehicle` fails with an error saying so when it is absent.

**Cargo is not expressible.** There is no `cargo` key at any level. FR-006 makes cargo the
unconsumed spaces remainder, so a file that could declare it would let a referee state a figure the
builder then contradicts.

**Armaments nest.** `[[mounts]]` carries `[[mounts.weapons]]` carries
`[[mounts.weapons.ammunition]]`. A magazine is a property of the weapon that fires it, so a magazine
without a weapon and a weapon outside a mount are not expressible in the file (FR-015). A mount with
no weapons is legal and costs what an empty mount costs.

**Unknown keys are rejected, per table.** `_reject_unknown(keys, allowed, path)` runs at the top of
each parse function, and the `path` it is given is the TOML-literal spelling, so the error names a
section a reader can find: `unknown key(s) in [[mounts.weapons]]: ['ammo']`. Dropping a key from an
allowed set is itself the migration message for a file written against an older shape.

**Round-tripping.** `dump_design` emits a fixed canonical key order, omits anything equal to its
model default, and writes every bare top-level scalar before the first table header, because a bare
key after a header would be read as a key of that table. This is how the fifteen catalog files are
authored and pinned, and it is what makes User Story 4's guarantee testable.

## Errors

| Raised | When |
|---|---|
| `ValueError` | Malformed TOML, re-raised as `malformed TOML: {detail}`. |
| `ValueError` | An unknown key, a wrong type, an unknown enum string, a missing required key. |
| `OSError` | Propagated unwrapped from `load_design` when the path cannot be read. |

No SRD rule violation is ever raised here.
