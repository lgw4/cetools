from __future__ import annotations

import difflib
from dataclasses import dataclass

from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.athlete import ATHLETE_CAREER
from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.belter import BELTER_CAREER
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER
from cetools.engine.careers.colonist import COLONIST_CAREER
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER
from cetools.engine.careers.drifter import DRIFTER_CAREER
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER
from cetools.engine.careers.hunter import HUNTER_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.maritime import MARITIME_CAREER
from cetools.engine.careers.mercenary import MERCENARY_CAREER
from cetools.engine.careers.merchant import MERCHANT_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.noble import NOBLE_CAREER
from cetools.engine.careers.physician import PHYSICIAN_CAREER
from cetools.engine.careers.pirate import PIRATE_CAREER
from cetools.engine.careers.rogue import ROGUE_CAREER
from cetools.engine.careers.scientist import SCIENTIST_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.careers.surface import SURFACE_CAREER
from cetools.engine.careers.technician import TECHNICIAN_CAREER

CAREERS: tuple[Career, ...] = tuple(
    sorted(
        (
            AEROSPACE_CAREER,
            AGENT_CAREER,
            ATHLETE_CAREER,
            BARBARIAN_CAREER,
            BELTER_CAREER,
            BUREAUCRAT_CAREER,
            COLONIST_CAREER,
            DIPLOMAT_CAREER,
            DRIFTER_CAREER,
            ENTERTAINER_CAREER,
            HUNTER_CAREER,
            MARINE_CAREER,
            MARITIME_CAREER,
            MERCENARY_CAREER,
            MERCHANT_CAREER,
            NAVY_CAREER,
            NOBLE_CAREER,
            PHYSICIAN_CAREER,
            PIRATE_CAREER,
            ROGUE_CAREER,
            SCIENTIST_CAREER,
            SCOUT_CAREER,
            SURFACE_CAREER,
            TECHNICIAN_CAREER,
        ),
        key=lambda career: career.name,
    )
)
"""Every career cetools implements, in name order."""

DRAFT_TABLE: tuple[Career, ...] = (
    AEROSPACE_CAREER,  # 1
    MARINE_CAREER,  # 2
    MARITIME_CAREER,  # 3
    NAVY_CAREER,  # 4
    SCOUT_CAREER,  # 5
    SURFACE_CAREER,  # 6
)
"""The six careers a drafted character can land in, indexed by 1D6 - 1.

Also the single source of truth for which careers are military: the military
careers are exactly the draftable uniformed services.
"""

_MILITARY: frozenset[Career] = frozenset(DRAFT_TABLE)

# A career is looked up by its own name, lowercased. There is no second
# identifier space: the key is derived, never authored.
_BY_KEY: dict[str, Career] = {career.name.lower(): career for career in CAREERS}

_SUGGESTION_CUTOFF = 0.6


@dataclass(frozen=True)
class UnknownCareer:
    """No career answers to `spec`. `suggestion` is the nearest one, if any."""

    spec: str
    suggestion: Career | None


def is_military(career: Career) -> bool:
    """Whether a career is one of the draftable military services."""
    return career in _MILITARY


def resolve(spec: str) -> Career | UnknownCareer:
    """The career a user asked for, however they typed it.

    Case and surrounding space do not matter, and a hyphen reads as a space, so
    `Aerospace-System-Defense` finds the same career as `aerospace system
    defense`. A near-miss comes back as a suggestion rather than an error string:
    what counts as a career's name is the engine's business, and what to print
    about it is the caller's.
    """
    key = spec.strip().lower().replace("-", " ")
    career = _BY_KEY.get(key)
    if career is not None:
        return career

    matches = difflib.get_close_matches(key, _BY_KEY, n=1, cutoff=_SUGGESTION_CUTOFF)
    return UnknownCareer(spec=spec, suggestion=_BY_KEY[matches[0]] if matches else None)
