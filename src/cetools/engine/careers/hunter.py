from cetools.engine.careers.base import Career, RankEntry

HUNTER_CAREER = Career(
    name="Hunter",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Strength",
    survival_target=8,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=6,
    service_skills=("Mechanics", "Gun Combat", "Melee Combat", "Recon", "Survival", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat"),
    specialist_skills=("Admin", "Comms", "Electronics", "Recon", "Animals", "Vehicle"),
    advanced_education=("Advocate", "Linguistics", "Medicine", "Liaison", "Animals", "Animals"),
    ranks=(RankEntry(0, "Hunter", ("Survival",)),),
    cash_benefits=(1000, 5000, 10000, 20000, 20000, 50000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "1D6 Ship Shares",
        "High Passage",
    ),
)
