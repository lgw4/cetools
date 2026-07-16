"""Rendering of UWP profile strings and full world-data lines."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cetools.engine.pseudohex import to_pseudohex

if TYPE_CHECKING:  # models.py imports this module, so only import it for types
    from cetools.engine.worlds.models import System, World


def render_profile(world: World) -> str:
    """The classic UWP string, e.g. `A867A9C-F` (research.md D5)."""
    digits = "".join(
        to_pseudohex(value)
        for value in (
            world.size,
            world.atmosphere,
            world.hydrographics,
            world.population,
            world.government,
            world.law_level,
        )
    )
    return f"{world.starport}{digits}-{to_pseudohex(world.tech_level)}"


def render_data_line(system: System) -> str:
    """The full, double-space-separated world-data line (research.md D5)."""
    fields = (
        system.world.name,
        system.hex if system.hex is not None else "",
        system.world.profile,
        system.base_code,
        " ".join(system.world.trade_codes),
        system.world.travel_zone.value,
        system.pbg,
        system.allegiance,
    )
    return "  ".join(fields)
