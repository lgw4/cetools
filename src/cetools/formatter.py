from cetools.engine.models import Character
from cetools.engine.pseudohex import to_pseudohex

_UPP_ORDER = (
    "Strength",
    "Dexterity",
    "Endurance",
    "Intelligence",
    "Education",
    "Social Standing",
)


def format_character(character: Character) -> str:
    lines = []

    lines.append(f"UPP: {character.upp}")
    lines.append("")
    lines.append(
        f"{character.career} ({character.rank_title}, Rank {character.rank})"
        f" — {character.terms_served} terms, age {character.age}"
    )
    lines.append("")

    lines.append("Characteristics:")
    for name in _UPP_ORDER:
        value = character.characteristics[name]
        if value > 9:
            ph = to_pseudohex(value)
            lines.append(f"  {name}: {value} ({ph})")
        else:
            lines.append(f"  {name}: {value}")
    lines.append("")

    lines.append("Skills:")
    skill_parts = [f"{name}-{level}" for name, level in sorted(character.skills.items())]
    lines.append(f"  {', '.join(skill_parts)}")
    lines.append("")

    cash_benefits = [b for b in character.benefits if b.kind == "cash"]
    material_benefits = [b for b in character.benefits if b.kind == "material"]
    lines.append("Mustering-Out Benefits:")
    if cash_benefits:
        cash_parts = [f"Cr{b.cash_amount:,}" for b in cash_benefits]
        lines.append(f"  Cash:     {', '.join(cash_parts)}")
    if material_benefits:
        material_parts = [b.material_name for b in material_benefits]
        lines.append(f"  Material: {', '.join(material_parts)}")

    if character.pension is not None:
        lines.append("")
        lines.append(f"Retirement Pension: Cr{character.pension:,}/year")

    return "\n".join(lines)
