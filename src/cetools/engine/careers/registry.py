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

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "agent": AGENT_CAREER,
    "athlete": ATHLETE_CAREER,
    "barbarian": BARBARIAN_CAREER,
    "belter": BELTER_CAREER,
    "bureaucrat": BUREAUCRAT_CAREER,
    "colonist": COLONIST_CAREER,
    "diplomat": DIPLOMAT_CAREER,
    "drifter": DRIFTER_CAREER,
    "entertainer": ENTERTAINER_CAREER,
    "hunter": HUNTER_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "mercenary": MERCENARY_CAREER,
    "merchant": MERCHANT_CAREER,
    "navy": NAVY_CAREER,
    "noble": NOBLE_CAREER,
    "physician": PHYSICIAN_CAREER,
    "pirate": PIRATE_CAREER,
    "rogue": ROGUE_CAREER,
    "scientist": SCIENTIST_CAREER,
    "scout": SCOUT_CAREER,
    "surface system defense": SURFACE_CAREER,
    "technician": TECHNICIAN_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "surface system defense",  # 6
)


def _collect_military_career_names(
    draft_table: tuple[str, ...], registry: dict[str, Career]
) -> frozenset[str]:
    """Return the display names of the draftable military careers.

    The military careers are exactly the draftable uniformed services, so
    ``draft_table`` is the single source of truth for that grouping. Any key
    without a matching registry career is reported explicitly, so a stray or
    misspelled ``DRAFT_TABLE`` entry fails with a clear message rather than a
    bare ``KeyError``.
    """
    missing = [key for key in draft_table if key not in registry]
    if missing:
        raise ValueError(f"DRAFT_TABLE references careers missing from CAREER_REGISTRY: {missing}")
    return frozenset(registry[key].name for key in draft_table)


MILITARY_CAREER_NAMES: frozenset[str] = _collect_military_career_names(
    DRAFT_TABLE, CAREER_REGISTRY
)


def is_military_career(name: str) -> bool:
    """Whether a career (by display name) is one of the draftable military services."""
    return name in MILITARY_CAREER_NAMES
