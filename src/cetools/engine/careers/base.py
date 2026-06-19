from dataclasses import dataclass

from cetools.engine.models import STAT_NAMES


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

    def __post_init__(self) -> None:
        valid_stats = set(STAT_NAMES)
        for field_name, stat in (
            ("qualification_stat", self.qualification_stat),
            ("survival_stat", self.survival_stat),
        ):
            if stat not in valid_stats:
                raise ValueError(
                    f"Career '{self.name}': {field_name} '{stat}' is not a valid stat"
                )
        for field_name, stat in (
            ("commission_stat", self.commission_stat),
            ("advancement_stat", self.advancement_stat),
        ):
            if stat is not None and stat not in valid_stats:
                raise ValueError(
                    f"Career '{self.name}': {field_name} '{stat}' is not a valid stat"
                )
        for table_name, table in (
            ("service_skills", self.service_skills),
            ("personal_development", self.personal_development),
            ("specialist_skills", self.specialist_skills),
            ("advanced_education", self.advanced_education),
        ):
            if len(table) != 6:
                raise ValueError(
                    f"Career '{self.name}': {table_name} must have exactly 6 entries,"
                    f" got {len(table)}"
                )
        if not (1 <= len(self.ranks) <= 7):
            raise ValueError(f"Career '{self.name}': must have 1–7 ranks, got {len(self.ranks)}")
        for i, rank_entry in enumerate(self.ranks):
            if rank_entry.rank != i:
                raise ValueError(
                    f"Career '{self.name}': rank at index {i}"
                    f" has rank={rank_entry.rank}, expected {i}"
                )
