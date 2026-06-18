from cetools.engine.careers.base import Career
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = ("navy", "navy", "navy", "navy", "scout", "navy")
