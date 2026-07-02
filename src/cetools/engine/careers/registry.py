from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "marine": MARINE_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",
    "marine",
    "navy",
    "navy",
    "scout",
    "navy",
)
