from dataclasses import dataclass


@dataclass(frozen=True)
class RankEntry:
    rank: int
    title: str
    bonus_skills: tuple[str, ...]


@dataclass(frozen=True)
class Career:
    name: str
    qualification_stat: str
    qualification_target: int
    survival_stat: str
    survival_target: int
    commission_stat: str | None
    commission_target: int | None
    advancement_stat: str | None
    advancement_target: int | None
    reenlistment_target: int
    service_skills: tuple[str, ...]
    personal_development: tuple[str, ...]
    specialist_skills: tuple[str, ...]
    advanced_education: tuple[str, ...]
    ranks: tuple[RankEntry, ...]
    cash_benefits: tuple[int, ...]
    material_benefits: tuple[str, ...]
