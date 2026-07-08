from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.athlete import ATHLETE_CAREER
from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER
from cetools.engine.careers.colonist import COLONIST_CAREER
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER
from cetools.engine.careers.drifter import DRIFTER_CAREER
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER
from cetools.engine.careers.hunter import HUNTER_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.maritime import MARITIME_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.noble import NOBLE_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.careers.surface import SURFACE_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "agent": AGENT_CAREER,
    "athlete": ATHLETE_CAREER,
    "barbarian": BARBARIAN_CAREER,
    "bureaucrat": BUREAUCRAT_CAREER,
    "colonist": COLONIST_CAREER,
    "diplomat": DIPLOMAT_CAREER,
    "drifter": DRIFTER_CAREER,
    "entertainer": ENTERTAINER_CAREER,
    "hunter": HUNTER_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "navy": NAVY_CAREER,
    "noble": NOBLE_CAREER,
    "scout": SCOUT_CAREER,
    "surface system defense": SURFACE_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "surface system defense",  # 6
)
