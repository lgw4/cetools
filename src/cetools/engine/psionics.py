from cetools.engine.dice import DiceRoller, as_rolls
from cetools.engine.models import characteristic_modifier
from cetools.engine.rolls import RollName, Rolls

# Talents in highest-Learning-DM-first attempt order (name, learning DM).
_TALENTS: tuple[tuple[str, int], ...] = (
    ("Telepathy", 4),
    ("Clairvoyance", 3),
    ("Telekinesis", 2),
    ("Awareness", 1),
    ("Teleportation", 0),
)

_TRAINING_TARGET = 8
_ELIGIBILITY_TARGET = 11


def roll_psionics(terms_served: int, roller: "DiceRoller | Rolls") -> tuple[int, dict[str, int]]:
    """Roll Psi strength and learn talents.

    A cetools house rule gates testing: the character must first pass a flat,
    unmodified ``2D6 >= 11`` eligibility check. On failure this returns
    ``(0, {})`` with no Psi or talent rolls. On success, Psi = 2D6 - terms_served,
    floored at 0. A character is psionic when Psi >= 1; only then are talents
    attempted. Each talent is a check
    ``2D6 + PsiDM + talentDM - (previous attempts) >= 8``; successes are granted
    at level 0. Talents are attempted highest-DM-first.
    """
    rolls = as_rolls(roller)

    if not rolls.check(0, _ELIGIBILITY_TARGET, RollName.PSI_GATE):
        return 0, {}

    psi_strength = max(0, rolls.two_d6(RollName.PSI_STRENGTH) - terms_served)
    talents: dict[str, int] = {}
    if psi_strength < 1:
        return psi_strength, talents

    psi_dm = characteristic_modifier(psi_strength)
    for attempt_index, (name, talent_dm) in enumerate(_TALENTS):
        dm = psi_dm + talent_dm - attempt_index
        if rolls.check(dm, _TRAINING_TARGET, RollName.PSI_TALENT):
            talents[name] = 0
    return psi_strength, talents
