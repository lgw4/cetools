"""SRD Chapter 12 world-generation tables, encoded as data."""

from __future__ import annotations

SIZE_DESCRIPTIONS: tuple[str, ...] = (
    "800 km, negligible gravity",
    "1,600 km, 0.05g",
    "3,200 km, 0.15g",
    "4,800 km, 0.25g",
    "6,400 km, 0.35g",
    "8,000 km, 0.45g",
    "9,600 km, 0.7g",
    "11,200 km, 0.9g",
    "12,800 km, 1.0g",
    "14,400 km, 1.25g",
    "16,000 km, 1.4g",
)
"""Diameter and surface gravity, indexed by the Size digit (Table: World Size)."""

ATMOSPHERE_DESCRIPTIONS: tuple[str, ...] = (
    "None",
    "Trace",
    "Very Thin, Tainted",
    "Very Thin",
    "Thin, Tainted",
    "Thin",
    "Standard",
    "Standard, Tainted",
    "Dense",
    "Dense, Tainted",
    "Exotic",
    "Corrosive",
    "Insidious",
    "Dense, High",
    "Thin, Low",
    "Unusual",
)
"""Atmosphere label, indexed by the Atmosphere digit (Table: Atmosphere)."""

HYDRO_DM_BY_ATMOSPHERE: dict[int, int] = {
    0: -4,
    1: -4,
    10: -4,
    11: -4,
    12: -4,
    14: -2,
}
"""Hydrographics DM keyed by Atmosphere; absent keys carry no DM."""

# Each rule fires when every listed field's value falls in its allowed set; a field
# absent from `conditions` is unconstrained. Multiple rules stack (the DMs sum).
POPULATION_DMS: tuple[dict, ...] = (
    {"conditions": {"size": frozenset(range(0, 3))}, "dm": -1},
    {"conditions": {"atmosphere": frozenset(range(10, 16))}, "dm": -2},
    {"conditions": {"atmosphere": frozenset({6})}, "dm": 3},
    {"conditions": {"atmosphere": frozenset({5, 8})}, "dm": 1},
    {
        "conditions": {
            "hydrographics": frozenset({0}),
            "atmosphere": frozenset(range(0, 3)),
        },
        "dm": -2,
    },
)
"""The five Population DM rules (Size <= 2; Atmosphere >= A/==6/==5,8; Hydro 0 & Atmo < 3)."""

STARPORT_BY_ROLL: dict[int, str] = {
    2: "X",
    3: "E",
    4: "E",
    5: "D",
    6: "D",
    7: "C",
    8: "C",
    9: "B",
    10: "B",
    11: "A",
}
"""Primary Starport table; the generator clamps its roll to this dict's 2-11 domain."""

GOVERNMENT_TYPES: tuple[str, ...] = (
    "None",
    "Company/Corporation",
    "Participating Democracy",
    "Self-Perpetuating Oligarchy",
    "Representative Democracy",
    "Feudal Technocracy",
    "Captive Government",
    "Balkanization",
    "Civil Service Bureaucracy",
    "Impersonal Bureaucracy",
    "Charismatic Dictator",
    "Non-Charismatic Leader",
    "Charismatic Oligarchy",
    "Religious Dictatorship",
    "Religious Autocracy",
    "Totalitarian Oligarchy",
)
"""Government type, indexed by the Government digit (Table: World Government)."""

LAW_LEVELS: tuple[str, ...] = (
    "No Law",
    "Low Law",
    "Low Law",
    "Low Law",
    "Medium Law",
    "Medium Law",
    "Medium Law",
    "High Law",
    "High Law",
    "High Law",
    "Extreme Law",
)
"""Law Level descriptor band, indexed 0-9 with index 10 standing for "10(A)+"."""

TL_DM_BY_VALUE: dict[str, dict[int | str, int]] = {
    "starport": {"A": 6, "B": 4, "C": 2, "X": -4},
    "size": {0: 2, 1: 2, 2: 1, 3: 1, 4: 1},
    "atmosphere": {0: 1, 1: 1, 2: 1, 3: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1},
    "hydrographics": {0: 1, 9: 1, 10: 2},
    "population": {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 9: 1, 10: 2, 11: 3, 12: 4},
    "government": {0: 1, 5: 1, 7: 2, 13: -2, 14: -2},
}
"""Technology Level DMs by UWP Values (Appendix C1), keyed by column then value."""

TL_MINIMUMS: tuple[dict, ...] = (
    {
        "conditions": {
            "hydrographics": frozenset({0, 10}),
            "population": frozenset(range(6, 11)),
        },
        "min": 4,
    },
    {"conditions": {"atmosphere": frozenset({4, 7, 9})}, "min": 5},
    {"conditions": {"atmosphere": frozenset({0, 1, 2, 3, 10, 11, 12})}, "min": 7},
    {
        "conditions": {
            "atmosphere": frozenset({13, 14}),
            "hydrographics": frozenset({10}),
        },
        "min": 7,
    },
)
"""Technology Level Minimums (Appendix C2); the highest matching minimum applies."""


TRADE_CODES: tuple[dict, ...] = (
    {
        "code": "Ag",
        "conditions": {
            "atmosphere": frozenset(range(4, 10)),
            "hydrographics": frozenset(range(4, 9)),
            "population": frozenset(range(5, 8)),
        },
    },
    {
        "code": "As",
        "conditions": {
            "size": frozenset({0}),
            "atmosphere": frozenset({0}),
            "hydrographics": frozenset({0}),
        },
    },
    {
        "code": "Ba",
        "conditions": {
            "population": frozenset({0}),
            "government": frozenset({0}),
            "law_level": frozenset({0}),
        },
    },
    {
        "code": "De",
        "conditions": {
            "atmosphere": frozenset(range(2, 16)),
            "hydrographics": frozenset({0}),
        },
    },
    {
        "code": "Fl",
        "conditions": {
            "atmosphere": frozenset(range(10, 16)),
            "hydrographics": frozenset(range(1, 11)),
        },
    },
    {
        "code": "Ga",
        "conditions": {
            "atmosphere": frozenset({5, 6, 8}),
            "hydrographics": frozenset(range(4, 10)),
            "population": frozenset(range(4, 9)),
        },
    },
    {"code": "Hi", "conditions": {"population": frozenset(range(9, 11))}},
    {"code": "Ht", "conditions": {"tech_level": frozenset(range(12, 34))}},
    {
        "code": "Ic",
        "conditions": {
            "atmosphere": frozenset({0, 1}),
            "hydrographics": frozenset(range(1, 11)),
        },
    },
    {
        "code": "In",
        "conditions": {
            "atmosphere": frozenset({0, 1, 2, 4, 7, 9}),
            "population": frozenset(range(9, 11)),
        },
    },
    {"code": "Lo", "conditions": {"population": frozenset(range(1, 4))}},
    {"code": "Lt", "conditions": {"tech_level": frozenset(range(0, 6))}},
    {
        "code": "Na",
        "conditions": {
            "atmosphere": frozenset(range(0, 4)),
            "hydrographics": frozenset(range(0, 4)),
            "population": frozenset(range(6, 11)),
        },
    },
    {"code": "Ni", "conditions": {"population": frozenset(range(4, 7))}},
    {
        "code": "Po",
        "conditions": {
            "atmosphere": frozenset(range(2, 6)),
            "hydrographics": frozenset(range(0, 4)),
        },
    },
    {
        "code": "Ri",
        "conditions": {
            "atmosphere": frozenset({6, 8}),
            "population": frozenset(range(6, 9)),
        },
    },
    {"code": "Wa", "conditions": {"hydrographics": frozenset({10})}},
    {"code": "Va", "conditions": {"atmosphere": frozenset({0})}},
)
"""UWP Values for Trade Codes (Appendix C3), in table order."""


def matches_conditions(conditions: dict[str, frozenset], values: dict[str, int]) -> bool:
    """Whether every field in `conditions` holds a value from its allowed set.

    The generic reader for the conditions-as-data rules above (`POPULATION_DMS`,
    `TL_MINIMUMS`, and their Phase 4 sibling `TRADE_CODES`): adding or correcting a
    rule needs no change here. A field missing from `conditions` is unconstrained.
    """
    return all(values[field] in allowed for field, allowed in conditions.items())
