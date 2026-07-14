from cetools.engine.careers.registry import is_military
from cetools.engine.models import Benefit, Cash, Character, Item, Shares, StatBoost
from cetools.engine.pseudohex import to_pseudohex

# Mishap wording by (military, discharge_type). Military careers keep the SRD's
# verbatim "discharged from the service" language; non-military careers get
# parallel civilian phrasing for the same mechanical outcome. The "dishonorable"
# case is resolved in _mishap_line because it also depends on imprisonment.
#
# Military status is not stored on the mishap; it is derived at render time by
# asking the character's career, whose source of truth is DRAFT_TABLE (see
# engine/careers/registry.py).
_MILITARY_DISCHARGE_TEXT = {
    "honorable": "Honorably discharged",
    "medical": "Medically discharged",
    "none": "Injured in action",
}

_CIVILIAN_DISCHARGE_TEXT = {
    "honorable": "Left the career in good standing",
    "medical": "Left the career due to injury",
    "none": "Injured in action",
}


def _combine_material_benefits(benefits: list[Benefit]) -> list[str]:
    """Material benefits as display strings, repeats collapsed.

    Benefits arrive already knowing what they are, so this only groups and counts.
    Each category keeps first-granted order, and the categories are laid out
    boosts, then single items, then repeated items, then ship shares.
    """
    boosts: dict[str, int] = {}
    items: dict[str, int] = {}
    shares = 0

    for benefit in benefits:
        match benefit:
            case StatBoost(label):
                boosts[label] = boosts.get(label, 0) + 1
            case Item(name):
                items[name] = items.get(name, 0) + 1
            case Shares(quantity):
                shares += quantity

    singles = [name for name, count in items.items() if count == 1]
    repeats = [f"{name} (x{count})" for name, count in items.items() if count > 1]

    return (
        [f"+{levels} {label}" for label, levels in boosts.items()]
        + singles
        + repeats
        + ([f"{shares} Ship Shares"] if shares else [])
    )


def _mishap_line(character: Character) -> str:
    mishap = character.mishap
    military = is_military(character.career)
    if mishap.discharge_type == "dishonorable":
        base = "Dishonorably discharged" if military else "Dismissed in disgrace"
        text = f"{base} (imprisoned)" if mishap.imprisoned else base
    elif military:
        text = _MILITARY_DISCHARGE_TEXT[mishap.discharge_type]
    else:
        text = _CIVILIAN_DISCHARGE_TEXT[mishap.discharge_type]

    if mishap.injury_reductions:
        injury_parts = [
            f"{stat} -{amount}" for stat, amount in sorted(mishap.injury_reductions.items())
        ]
        text += f", injured ({', '.join(injury_parts)})"

    if mishap.injury_crisis:
        text += ", survived an injury crisis"

    if character.debt != 0:
        text += f"; Debt Cr{character.debt:,}"

    return f"Mishap: {text}"


def format_character(character: Character) -> str:
    rank_prefix = f"{character.rank_title} " if character.rank_title else ""
    upp_display = character.upp
    if character.psi_strength >= 1:
        upp_display += f"-{to_pseudohex(character.psi_strength)}"
    line1 = f"{rank_prefix}{character.name}\t{upp_display}\tAge {character.age}"

    funds = sum(b.amount for b in character.benefits if isinstance(b, Cash))
    line2 = f"{character.career.name} ({character.terms_served} terms)\tCr{funds:,}"

    skill_parts = [f"{name}-{level}" for name, level in sorted(character.skills.items())]
    line3 = ", ".join(skill_parts)

    lines = [line1, line2, line3]

    if character.talents:
        talent_parts = [f"{name}-{level}" for name, level in sorted(character.talents.items())]
        lines.append("Psionics: " + ", ".join(talent_parts))

    material_parts = _combine_material_benefits(character.benefits)
    if material_parts:
        lines.append(", ".join(material_parts))

    if character.mishap is not None:
        lines.append(_mishap_line(character))

    return "\n".join(lines)


def format_characters(characters: list[Character]) -> str:
    return "\n\n".join(format_character(character) for character in characters)
