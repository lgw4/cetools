from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.maritime import MARITIME_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "navy",  # 6: placeholder for Surface System Defense (not yet implemented)
)
