from cetools.engine.careers.base import Career, RankEntry

BELTER_CAREER = Career(
    name="Belter",
    qualification_stat="Intelligence",
    qualification_target=4,
    survival_stat="Dexterity",
    survival_target=7,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=5,
    service_skills=("Comms", "Demolitions", "Gun Combat", "Gunnery", "Prospecting", "Piloting"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Zero-G", "Melee Combat", "Gambling"),
    specialist_skills=("Zero-G", "Electronics", "Prospecting", "Sciences", "Vehicle", "Vehicle"),
    advanced_education=("Advocate", "Engineering", "Medicine", "Navigation", "Comms", "Tactics"),
    ranks=(RankEntry(0, "Belter", ()),),
    cash_benefits=(1000, 5000, 5000, 5000, 10000, 20000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "1D6 Ship Shares",
        "High Passage",
    ),
)
