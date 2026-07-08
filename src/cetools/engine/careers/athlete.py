from cetools.engine.careers.base import Career, RankEntry

ATHLETE_CAREER = Career(
    name="Athlete",
    qualification_stat="Endurance",
    qualification_target=8,
    survival_stat="Dexterity",
    survival_target=5,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=6,
    service_skills=("Athletics", "Admin", "Carousing", "Computer", "Gambling", "Vehicle"),
    personal_development=("+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat"),
    specialist_skills=("Zero-G", "Athletics", "Athletics", "Computer", "Leadership", "Gambling"),
    advanced_education=("Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Sciences"),
    ranks=(RankEntry(0, "Athlete", ("Athletics",)),),
    cash_benefits=(2000, 10000, 20000, 20000, 50000, 100000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "Explorers' Society",
        "High Passage",
    ),
)
