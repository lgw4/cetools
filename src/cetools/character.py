from typing import (Dict, Optional)

import attr


@attr.s(auto_attribs=True)
class Character:
    name: str
    strength: int
    dexterity: int
    endurance: int
    intelligence: int
    education: int
    social_standing: int
    psionic_strength: Optional[int]
    careers: Dict[str, int]
    skills: Dict[str, int]
