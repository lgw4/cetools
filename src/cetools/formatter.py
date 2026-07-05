from cetools.engine.models import Character

_DISCHARGE_TEXT = {
    "honorable": "Honorably discharged",
    "medical": "Medically discharged",
    "none": "Injured in action",
}


def _mishap_line(character: Character) -> str:
    mishap = character.mishap
    if mishap.discharge_type == "dishonorable":
        text = (
            "Dishonorably discharged (imprisoned)"
            if mishap.imprisoned
            else "Dishonorably discharged"
        )
    else:
        text = _DISCHARGE_TEXT[mishap.discharge_type]

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
    line1 = f"{rank_prefix}{character.name}\t{character.upp}\tAge {character.age}"

    funds = sum(b.cash_amount for b in character.benefits if b.kind == "cash")
    line2 = f"{character.career} ({character.terms_served} terms)\tCr{funds:,}"

    skill_parts = [f"{name}-{level}" for name, level in sorted(character.skills.items())]
    line3 = ", ".join(skill_parts)

    lines = [line1, line2, line3]

    material_parts = [b.material_name for b in character.benefits if b.kind == "material"]
    if material_parts:
        lines.append(", ".join(material_parts))

    if character.mishap is not None:
        lines.append(_mishap_line(character))

    return "\n".join(lines)
