from cetools.engine.models import Benefit, Character
from cetools.engine.pseudohex import to_pseudohex

_DISCHARGE_TEXT = {
    "honorable": "Honorably discharged",
    "medical": "Medically discharged",
    "none": "Injured in action",
}


def _combine_material_benefits(benefits: list[Benefit]) -> list[str]:
    boost_totals: dict[str, int] = {}
    boost_first_index: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    item_first_index: dict[str, int] = {}
    quantity_totals: dict[str, int] = {}
    quantity_first_index: dict[str, int] = {}

    index = 0
    for benefit in benefits:
        if benefit.kind != "material":
            continue
        name = benefit.material_name
        if benefit.material_quantity is not None:
            quantity_totals[name] = quantity_totals.get(name, 0) + benefit.material_quantity
            quantity_first_index.setdefault(name, index)
        elif name.startswith("+1 "):
            label = name[3:]
            boost_totals[label] = boost_totals.get(label, 0) + 1
            boost_first_index.setdefault(label, index)
        else:
            item_counts[name] = item_counts.get(name, 0) + 1
            item_first_index.setdefault(name, index)
        index += 1

    boosts = [
        f"+{boost_totals[label]} {label}"
        for label in sorted(boost_totals, key=lambda label: boost_first_index[label])
    ]
    singles = sorted(
        (name for name, count in item_counts.items() if count == 1),
        key=lambda name: item_first_index[name],
    )
    repeats = sorted(
        (name for name, count in item_counts.items() if count > 1),
        key=lambda name: item_first_index[name],
    )
    quantities = [
        f"{quantity_totals[name]} {name}"
        for name in sorted(quantity_totals, key=lambda name: quantity_first_index[name])
    ]

    return boosts + singles + [f"{name} (x{item_counts[name]})" for name in repeats] + quantities


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
    upp_display = character.upp
    if character.psi_strength >= 1:
        upp_display += f"-{to_pseudohex(character.psi_strength)}"
    line1 = f"{rank_prefix}{character.name}\t{upp_display}\tAge {character.age}"

    funds = sum(b.cash_amount for b in character.benefits if b.kind == "cash")
    line2 = f"{character.career} ({character.terms_served} terms)\tCr{funds:,}"

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
