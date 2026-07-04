from cetools.engine.models import Character


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

    return "\n".join(lines)
