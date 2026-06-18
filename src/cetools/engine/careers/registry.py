from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",
    "navy",
    "navy",
    "navy",
    "scout",
    "navy",
)
