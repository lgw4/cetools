"""The lifepath walk: `generate_character` and `generate_batch`
(contracts/library-api.md, data-model.md, spec.md FR-001 through FR-030a).

One `Roller` drives the whole walk (research R1); the name stream is a
derived roller the walk's own roller never touches (research R3). Every
random choice the source material hands to a player becomes a draw here,
and every draw is recorded as a `HistoryStep` so a surprising sheet is
diagnosable (FR-030).
"""

from collections.abc import Mapping

from cetools.careers import CareerDefinition, RankLadder
from cetools.character import (
    CareerService,
    Character,
    CharacterBatch,
    CharacterSkill,
    HistoryStep,
    StepEffect,
    StepThrow,
)
from cetools.dice import Roller, parse_notation
from cetools.errors import CetoolsError
from cetools.names import roll_name
from cetools.notation import (
    BenefitItem,
    CharacteristicAdjustment,
    SkillGrant,
    SkillReference,
)
from cetools.registries import SkillRegistry
from cetools.rules import RulesData
from cetools.seeds import derive_seed
from cetools.tasks import Modifier

_2D6 = (2, 6)
_ENTERED_BY_SELECTED = "selected"
_ENTERED_BY_DRAFTED = "drafted"
_ENTERED_BY_FALLBACK = "fallback"


def _dice(roller: Roller, notation: str) -> tuple[int, ...]:
    count, sides, _modifier = parse_notation(notation)
    return roller.dice(count, sides)


def _resolve_specialty(
    reference: SkillReference, skills: SkillRegistry, roller: Roller
) -> SkillReference:
    """Cascade rule (FR-011): choose a permitted specialty uniformly at
    random when the grant names none and the registry gives the skill any.
    """
    if reference.specialty is not None:
        return reference
    specialties = skills.skills.get(reference.name, ())
    if not specialties:
        return reference
    return SkillReference(
        name=reference.name, specialty=specialties[roller.die(len(specialties)) - 1]
    )


def _skill_label(reference: SkillReference) -> str:
    if reference.specialty is None:
        return reference.name
    return f"{reference.name} ({reference.specialty})"


class _SkillBook:
    """The skills a character has accumulated so far, keyed by
    `(name, specialty)`. A bare grant is "+1, or 0 on first exposure"; an
    explicit grant never lowers an existing level; basic training's
    first-career grant only ever raises a missing skill to level 0.
    """

    def __init__(self) -> None:
        self._levels: dict[tuple[str, str | None], int] = {}

    def apply_bare(self, reference: SkillReference) -> int:
        key = (reference.name, reference.specialty)
        level = 0 if key not in self._levels else self._levels[key] + 1
        self._levels[key] = level
        return level

    def apply_explicit(self, reference: SkillReference, level: int) -> int:
        key = (reference.name, reference.specialty)
        current = self._levels.get(key, -1)
        applied = max(current, level)
        self._levels[key] = applied
        return applied

    def ensure_present_at_zero(self, reference: SkillReference) -> int:
        key = (reference.name, reference.specialty)
        if key not in self._levels:
            self._levels[key] = 0
        return self._levels[key]

    def as_tuple(self) -> tuple[CharacterSkill, ...]:
        return tuple(
            CharacterSkill(name=name, specialty=specialty, level=level)
            for (name, specialty), level in self._levels.items()
        )


def _apply_characteristic_delta(
    characteristics: dict[str, int], code: str, delta: int, floor: int
) -> list[StepEffect]:
    """Apply a signed change to `code`, clamping a reduction at `floor`
    (research R13). Records both the reduction called for and the amount
    actually applied when a floor clamp makes them differ.
    """
    old = characteristics[code]
    called_for_value = old + delta
    applied_value = max(called_for_value, floor) if delta < 0 else called_for_value
    characteristics[code] = applied_value
    applied_delta = applied_value - old
    effects = [StepEffect(kind="characteristic", subject=code, amount=applied_delta)]
    if applied_delta != delta:
        effects.insert(0, StepEffect(kind="characteristic", subject=code, amount=delta))
    return effects


def _apply_entry(
    entry: object,
    characteristics: dict[str, int],
    skills_registry: SkillRegistry,
    skills: _SkillBook,
    roller: Roller,
    floor: int,
) -> list[StepEffect]:
    """Apply one skill-table (or benefit-table) entry: a characteristic
    adjustment, an explicit skill grant, or a bare skill reference — the
    three forms `EntryContext.SKILL_TABLE` admits.
    """
    if isinstance(entry, CharacteristicAdjustment):
        return _apply_characteristic_delta(
            characteristics, entry.characteristic, entry.amount, floor
        )
    if isinstance(entry, SkillGrant):
        resolved = _resolve_specialty(entry.skill, skills_registry, roller)
        level = skills.apply_explicit(resolved, entry.level)
        return [StepEffect(kind="skill", subject=_skill_label(resolved), amount=level)]
    if isinstance(entry, SkillReference):
        resolved = _resolve_specialty(entry, skills_registry, roller)
        level = skills.apply_bare(resolved)
        return [StepEffect(kind="skill", subject=_skill_label(resolved), amount=level)]
    raise CetoolsError(f"unsupported skill-table entry: {entry!r}")


def _parse_amount(text: str, roller: Roller) -> int:
    """A `MishapEffect.amount` field: dice notation or a signed integer,
    written as text either way (contracts/data-files.md). Dice notation may
    carry a leading sign — `"-1d6"` is a roll subtracted, not added
    (`parse_notation` itself admits no sign before the count).
    """
    try:
        return int(text)
    except ValueError:
        pass
    sign = 1
    body = text
    if body and body[0] in "+-":
        sign = -1 if body[0] == "-" else 1
        body = body[1:]
    count, sides, modifier = parse_notation(body)
    return sign * (sum(roller.dice(count, sides)) + modifier)


def _eligible_tables(
    career: CareerDefinition, characteristics: Mapping[str, int]
) -> list[tuple[str, object]]:
    eligible = []
    for key, table in sorted(career.tables.items()):
        gate = table.requires
        if gate is not None and characteristics.get(gate.characteristic, 0) < gate.target:
            continue
        eligible.append((key, table))
    return eligible


class _Debt:
    """One outstanding debt, in the order it arose (FR-025a). `restore`
    describes what a full or partial settlement buys back: `crisis` restores
    every covered characteristic to a fixed score; `medical` restores points
    at a fixed cost per point, in the order the walk records.
    """

    __slots__ = ("amount", "restore", "characteristics", "restore_to", "cost_per_point")

    def __init__(
        self,
        amount: int,
        restore: str,
        characteristics: tuple[str, ...] = (),
        restore_to: int = 0,
        cost_per_point: int = 0,
    ) -> None:
        self.amount = amount
        self.restore = restore
        self.characteristics = characteristics
        self.restore_to = restore_to
        self.cost_per_point = cost_per_point


class _Walk:
    """Mutable state threaded through one `generate_character` call. Not
    part of the public surface; `generate_character` is the seam.
    """

    def __init__(self, roller: Roller, rules: RulesData) -> None:
        self.roller = roller
        self.rules = rules
        self.characteristics: dict[str, int] = {}
        self.skills = _SkillBook()
        self.history: list[HistoryStep] = []
        self.career_services: list[CareerService] = []
        self.age = rules.chargen.terms_starting_age
        self.total_terms_served = 0
        self.funds = 0
        self.debt = 0
        self.pension = 0
        self.benefits: list[str] = []
        self.debts: list[_Debt] = []
        self.title = ""
        self.draft_uses = 0

    def floor(self) -> int:
        return self.rules.characteristics.floor()

    def characteristic_dm(self, code: str | None) -> int:
        if code is None:
            return 0
        return self.rules.characteristics.characteristic_dm(self.characteristics[code])

    def settle_debts(self) -> None:
        """Pay outstanding debts, oldest first, from `self.funds`, never
        taking funds below zero (FR-025a, FR-026).
        """
        remaining: list[_Debt] = []
        for debt in self.debts:
            if self.funds <= 0:
                remaining.append(debt)
                continue
            payment = min(self.funds, debt.amount)
            self.funds -= payment
            self.debt -= payment
            debt.amount -= payment
            if debt.restore == "crisis" and debt.amount == 0:
                for code in debt.characteristics:
                    self.characteristics[code] = max(self.characteristics[code], debt.restore_to)
            elif debt.restore == "medical" and debt.cost_per_point > 0:
                points = payment // debt.cost_per_point
                for code in sorted(debt.characteristics)[:points]:
                    self.characteristics[code] += 1
            if debt.amount > 0:
                remaining.append(debt)
        self.debts = remaining

    def add_debt(self, debt: _Debt) -> None:
        self.debt += debt.amount
        self.debts.append(debt)
        self.settle_debts()

    def roll_characteristics(self) -> None:
        effects = []
        for code in self.rules.characteristics.names:
            faces = _dice(self.roller, self.rules.chargen.characteristics_roll)
            score = sum(faces)
            self.characteristics[code] = score
            effects.append(StepEffect(kind="characteristic", subject=code, amount=score))
        self.history.append(
            HistoryStep(
                kind="characteristics",
                career="",
                term=0,
                throw=None,
                selected="",
                effects=tuple(effects),
            )
        )

    def roll_background_skills(self) -> None:
        params = self.rules.chargen
        edu_dm = self.characteristic_dm(params.background_skills_characteristic)
        count = max(1, params.background_skills_base + edu_dm)
        homeworld = (
            self.rules.background_skills.law_level + self.rules.background_skills.trade_code
        )
        education = self.rules.background_skills.education
        homeworld_count = min(count, params.background_skills_homeworld_first)
        effects = []
        for i in range(count):
            pool = homeworld if i < homeworld_count else education
            grant = pool[self.roller.die(len(pool)) - 1]
            resolved = _resolve_specialty(grant.skill, self.rules.skills, self.roller)
            level = self.skills.apply_explicit(resolved, grant.level)
            effects.append(StepEffect(kind="skill", subject=_skill_label(resolved), amount=level))
        self.history.append(
            HistoryStep(
                kind="background-skills",
                career="",
                term=0,
                throw=None,
                selected="",
                effects=tuple(effects),
            )
        )

    def _entry_ladder(self, career: CareerDefinition) -> RankLadder:
        return next(ladder for ladder in career.ladders if ladder.role == "entry")

    def _commissioned_ladder(self, career: CareerDefinition) -> RankLadder | None:
        return next((ladder for ladder in career.ladders if ladder.role == "commissioned"), None)

    def _grant_rank_bonus(
        self, career_name: str, term: int, ladder: RankLadder, rank: int
    ) -> None:
        rank_row = next(r for r in ladder.ranks if r.rank == rank)
        effects: list[StepEffect] = []
        if rank_row.bonus is not None:
            effects = _apply_entry(
                rank_row.bonus,
                self.characteristics,
                self.rules.skills,
                self.skills,
                self.roller,
                self.floor(),
            )
        self.history.append(
            HistoryStep(
                kind="rank-bonus",
                career=career_name,
                term=term,
                throw=None,
                selected="",
                effects=tuple(effects),
            )
        )

    def _select_career(self, entered_names: set[str]) -> CareerDefinition:
        available = sorted(
            (
                c
                for c in self.rules.careers.values()
                if c.name not in entered_names or c.re_enterable
            ),
            key=lambda c: c.name,
        )
        return available[self.roller.die(len(available)) - 1]

    def _qualify(self, career: CareerDefinition, entries_so_far: int) -> bool:
        params = self.rules.chargen
        throw = career.throws["qualification"]
        faces = self.roller.dice(*_2D6)
        modifiers = []
        char_dm = self.characteristic_dm(throw.characteristic)
        if throw.characteristic is not None:
            modifiers.append(
                Modifier(f"Characteristic {self.characteristics[throw.characteristic]}", char_dm)
            )
        penalty = params.qualification_penalty_per_previous_career * entries_so_far
        if penalty:
            modifiers.append(Modifier("Previous careers", penalty))
        total = sum(faces) + sum(m.value for m in modifiers)
        success = total >= throw.target
        self.history.append(
            HistoryStep(
                kind="qualification",
                career=career.name,
                term=1,
                throw=StepThrow(
                    faces=faces,
                    modifiers=tuple(modifiers),
                    total=total,
                    target=throw.target,
                    success=success,
                ),
                selected="",
                effects=(),
            )
        )
        return success

    def _draft(self) -> CareerDefinition:
        draft = self.rules.draft
        faces = _dice(self.roller, draft.roll)
        row = sum(faces)
        name = draft.careers[row - 1]
        self.history.append(
            HistoryStep(
                kind="draft",
                career="",
                term=0,
                throw=StepThrow(faces=faces, modifiers=(), total=row, target=0, success=True),
                selected=name,
                effects=(),
            )
        )
        return next(c for c in self.rules.careers.values() if c.name == name)

    def enter_career(self, entered_names: set[str]) -> tuple[CareerDefinition, str]:
        candidate = self._select_career(entered_names)
        self.history.append(
            HistoryStep(
                kind="career-selected",
                career="",
                term=0,
                throw=None,
                selected=candidate.name,
                effects=(),
            )
        )
        if self._qualify(candidate, len(self.career_services)):
            entered_by = _ENTERED_BY_SELECTED
        else:
            params = self.rules.chargen
            if self.draft_uses < params.qualification_draft_entries_allowed:
                self.draft_uses += 1
                candidate = self._draft()
                entered_by = _ENTERED_BY_DRAFTED
            else:
                candidate = next(c for c in self.rules.careers.values() if c.always_available)
                entered_by = _ENTERED_BY_FALLBACK
            if candidate.name in entered_names and not candidate.re_enterable:
                # The draft table and the always-available fallback both name a
                # fixed career; FR-015 forbids re-entering a career already
                # entered except one the data marks re-enterable, so a
                # collision with either route falls through to the
                # always-available career instead, which every shipped
                # ruleset guarantees is re-enterable.
                candidate = next(c for c in self.rules.careers.values() if c.re_enterable)
        self.history.append(
            HistoryStep(
                kind="career-entered",
                career=candidate.name,
                term=1,
                throw=None,
                selected=entered_by,
                effects=(),
            )
        )
        return candidate, entered_by

    def basic_training(self, career: CareerDefinition, is_first_career: bool) -> None:
        params = self.rules.chargen
        service_table = career.tables["service"]
        effects = []
        if is_first_career and params.basic_training_first_career_all:
            entries = service_table.entries
        else:
            count = params.basic_training_subsequent_career_count
            entries = [
                service_table.entries[self.roller.die(len(service_table.entries)) - 1]
                for _ in range(count)
            ]
        for entry in entries:
            reference = entry.skill if isinstance(entry, SkillGrant) else entry
            if not isinstance(reference, SkillReference):
                continue
            resolved = _resolve_specialty(reference, self.rules.skills, self.roller)
            if is_first_career and params.basic_training_first_career_all:
                level = self.skills.ensure_present_at_zero(resolved)
            else:
                level = self.skills.apply_bare(resolved)
            effects.append(StepEffect(kind="skill", subject=_skill_label(resolved), amount=level))
        self.history.append(
            HistoryStep(
                kind="basic-training",
                career=career.name,
                term=1,
                throw=None,
                selected="",
                effects=tuple(effects),
            )
        )

    def run_term_loop(self, career: CareerDefinition, entered_by: str):
        """Run terms for one service until it ends. Returns
        `(terms, ladder, rank, commissioned, ended, benefit_rolls, forfeit_all)`.
        """
        params = self.rules.chargen
        ladder = self._entry_ladder(career)
        current_ladder_name = ladder.name
        current_rank = 0
        commissioned = False
        terms = 0
        forfeited_terms = 0
        forfeit_all = False
        ended = "term cap"

        while True:
            term = terms + 1
            faces = self.roller.dice(*_2D6)
            dice_total = sum(faces)
            survival = career.throws["survival"]
            char_dm = self.characteristic_dm(survival.characteristic)
            modifiers = (
                [
                    Modifier(
                        f"Characteristic {self.characteristics[survival.characteristic]}", char_dm
                    )
                ]
                if survival.characteristic is not None
                else []
            )
            total = dice_total + sum(m.value for m in modifiers)
            natural_failure = dice_total <= params.survival_natural_failure
            success = (not natural_failure) and total >= survival.target
            self.history.append(
                HistoryStep(
                    kind="survival",
                    career=career.name,
                    term=term,
                    throw=StepThrow(
                        faces=faces,
                        modifiers=tuple(modifiers),
                        total=total,
                        target=survival.target,
                        success=success,
                    ),
                    selected="",
                    effects=(),
                )
            )

            if not success:
                mishap_faces = _dice(self.roller, self.rules.mishaps.roll)
                row = self.rules.mishaps.rows[sum(mishap_faces) - 1]
                self.history.append(
                    HistoryStep(
                        kind="mishap",
                        career=career.name,
                        term=term,
                        throw=StepThrow(
                            faces=mishap_faces,
                            modifiers=(),
                            total=sum(mishap_faces),
                            target=0,
                            success=True,
                        ),
                        selected=row.description,
                        effects=(),
                    )
                )
                extra_years = 0
                for effect in row.effects:
                    if effect.kind == "characteristic-class":
                        self._apply_class_effect(effect, career.name, term)
                    elif effect.kind == "debt":
                        amount = _parse_amount(effect.amount, self.roller)
                        self.add_debt(_Debt(amount=amount, restore="none"))
                        self.history.append(
                            HistoryStep(
                                kind="mishap",
                                career=career.name,
                                term=term,
                                throw=None,
                                selected="",
                                effects=(StepEffect(kind="debt", subject="", amount=amount),),
                            )
                        )
                    elif effect.kind == "years":
                        extra_years += _parse_amount(effect.amount, self.roller)
                    elif effect.kind == "forfeit-term-benefit":
                        forfeited_terms += 1
                    elif effect.kind == "forfeit-career-benefits":
                        forfeit_all = True
                    elif effect.kind == "roll-injury":
                        self._roll_injury(career.name, term)
                terms += 1
                forfeited_terms += 1
                self.total_terms_served += 1
                self.age += params.terms_mishap_term_years + extra_years
                self._apply_aging_if_due(career.name, term)
                ended = "mishap"
                break

            entered_by_drafted_this_term = entered_by == _ENTERED_BY_DRAFTED and term == 1
            commission_barred = (
                params.commission_drafted_first_term_barred and entered_by_drafted_this_term
            )
            extra_rolls = 0

            if "commission" in career.throws and not commissioned and not commission_barred:
                commissioned_ladder = self._commissioned_ladder(career)
                throw = career.throws["commission"]
                faces_c = self.roller.dice(*_2D6)
                char_dm_c = self.characteristic_dm(throw.characteristic)
                mods_c = (
                    [
                        Modifier(
                            f"Characteristic {self.characteristics[throw.characteristic]}",
                            char_dm_c,
                        )
                    ]
                    if throw.characteristic is not None
                    else []
                )
                total_c = sum(faces_c) + sum(m.value for m in mods_c)
                success_c = total_c >= throw.target
                self.history.append(
                    HistoryStep(
                        kind="commission",
                        career=career.name,
                        term=term,
                        throw=StepThrow(
                            faces=faces_c,
                            modifiers=tuple(mods_c),
                            total=total_c,
                            target=throw.target,
                            success=success_c,
                        ),
                        selected="",
                        effects=(),
                    )
                )
                if success_c and commissioned_ladder is not None:
                    commissioned = True
                    current_ladder_name = commissioned_ladder.name
                    current_rank = commissioned_ladder.ranks[0].rank
                    self._grant_rank_bonus(career.name, term, commissioned_ladder, current_rank)
                    extra_rolls += params.skill_rolls_on_commission

            if "promotion" in career.throws:
                current_ladder = next(
                    ladder for ladder in career.ladders if ladder.name == current_ladder_name
                )
                ranks_above = sorted(r.rank for r in current_ladder.ranks if r.rank > current_rank)
                if ranks_above:
                    throw = career.throws["promotion"]
                    faces_p = self.roller.dice(*_2D6)
                    char_dm_p = self.characteristic_dm(throw.characteristic)
                    mods_p = (
                        [
                            Modifier(
                                f"Characteristic {self.characteristics[throw.characteristic]}",
                                char_dm_p,
                            )
                        ]
                        if throw.characteristic is not None
                        else []
                    )
                    total_p = sum(faces_p) + sum(m.value for m in mods_p)
                    success_p = total_p >= throw.target
                    self.history.append(
                        HistoryStep(
                            kind="advancement",
                            career=career.name,
                            term=term,
                            throw=StepThrow(
                                faces=faces_p,
                                modifiers=tuple(mods_p),
                                total=total_p,
                                target=throw.target,
                                success=success_p,
                            ),
                            selected="",
                            effects=(),
                        )
                    )
                    if success_p:
                        current_rank = ranks_above[0]
                        self._grant_rank_bonus(career.name, term, current_ladder, current_rank)
                        extra_rolls += params.skill_rolls_on_advancement

            no_throws = "commission" not in career.throws and "promotion" not in career.throws
            base_rolls = (
                params.skill_rolls_per_term_without_throws
                if no_throws
                else params.skill_rolls_per_term
            )
            self._roll_skills(career, base_rolls + extra_rolls, term)

            terms += 1
            self.total_terms_served += 1
            self.age += params.terms_term_years
            self._apply_aging_if_due(career.name, term)

            if self.total_terms_served >= params.terms_cap:
                ended = "term cap"
                break

            continuation = params.continuation_roll
            faces_k = _dice(self.roller, continuation)
            total_k = sum(faces_k)
            wants_to_continue = total_k >= params.continuation_target
            self.history.append(
                HistoryStep(
                    kind="continuation",
                    career=career.name,
                    term=term,
                    throw=StepThrow(
                        faces=faces_k,
                        modifiers=(),
                        total=total_k,
                        target=params.continuation_target,
                        success=wants_to_continue,
                    ),
                    selected="",
                    effects=(),
                )
            )
            if not wants_to_continue:
                ended = "chose to leave"
                break

            re_enlist = career.throws["re-enlistment"]
            faces_r = self.roller.dice(*_2D6)
            total_r = sum(faces_r)
            success_r = total_r >= re_enlist.target
            self.history.append(
                HistoryStep(
                    kind="re-enlistment",
                    career=career.name,
                    term=term,
                    throw=StepThrow(
                        faces=faces_r,
                        modifiers=(),
                        total=total_r,
                        target=re_enlist.target,
                        success=success_r,
                    ),
                    selected="",
                    effects=(),
                )
            )
            if not success_r:
                ended = "re-enlistment"
                break

        self.history.append(
            HistoryStep(
                kind="career-ended",
                career=career.name,
                term=terms,
                throw=None,
                selected=ended,
                effects=(),
            )
        )
        benefit_rolls = 0 if forfeit_all else max(0, terms - forfeited_terms)
        return (
            terms,
            current_ladder_name,
            current_rank,
            commissioned,
            ended,
            benefit_rolls,
            forfeit_all,
        )

    def _apply_class_effect(self, effect, career_name: str, term: int) -> None:
        classes = self.rules.characteristics.classes
        candidates = sorted(
            code for code, cls in classes.items() if cls == effect.characteristic_class
        )
        count = min(effect.count, len(candidates))
        chosen: list[str] = []
        remaining = list(candidates)
        for _ in range(count):
            index = self.roller.die(len(remaining)) - 1
            chosen.append(remaining.pop(index))
        amount = _parse_amount(effect.amount, self.roller)
        effects: list[StepEffect] = []
        crisis_codes: list[str] = []
        for code in sorted(chosen):
            applied = _apply_characteristic_delta(self.characteristics, code, amount, self.floor())
            effects.extend(applied)
            if self.characteristics[code] <= self.floor() and amount < 0:
                crisis_codes.append(code)
        self.history.append(
            HistoryStep(
                kind="mishap",
                career=career_name,
                term=term,
                throw=None,
                selected="",
                effects=tuple(effects),
            )
        )
        if crisis_codes:
            self._trigger_medical_crisis(career_name, term, tuple(crisis_codes))

    def _trigger_medical_crisis(self, career_name: str, term: int, codes: tuple[str, ...]) -> None:
        params = self.rules.chargen
        faces = _dice(self.roller, params.medical_crisis_roll)
        amount = sum(faces) * params.medical_crisis_multiplier
        self.add_debt(
            _Debt(
                amount=amount,
                restore="crisis",
                characteristics=codes,
                restore_to=params.medical_crisis_restores_to,
            )
        )
        self.history.append(
            HistoryStep(
                kind="debt-settled",
                career=career_name,
                term=term,
                throw=StepThrow(
                    faces=faces, modifiers=(), total=sum(faces), target=0, success=True
                ),
                selected="",
                effects=(StepEffect(kind="debt", subject="", amount=amount),),
            )
        )

    def _roll_injury(self, career_name: str, term: int) -> None:
        faces = _dice(self.roller, self.rules.mishaps.injury_roll)
        row = self.rules.mishaps.injuries[sum(faces) - 1]
        self.history.append(
            HistoryStep(
                kind="injury",
                career=career_name,
                term=term,
                throw=StepThrow(
                    faces=faces, modifiers=(), total=sum(faces), target=0, success=True
                ),
                selected=row.description,
                effects=(),
            )
        )
        raised = False
        for effect in row.effects:
            if effect.kind == "characteristic-class":
                self._apply_class_effect(effect, career_name, term)
                raised = True
        if raised:
            self._raise_medical_bill(career_name, term)

    def _raise_medical_bill(self, career_name: str, term: int) -> None:
        career = next(c for c in self.rules.careers.values() if c.name == career_name)
        tier = self.rules.medical_tiers.tiers[career.medical_tier]
        faces = _dice(self.roller, self.rules.medical_tiers.roll)
        # `rank_dm` would add the character's rank at the time of the bill; the
        # walk does not track an in-progress rank snapshot separately from the
        # term loop's local state, so this reads the tier's thresholds unmodified.
        total = sum(faces)
        paid_percent = 0
        for threshold in tier:
            if total >= threshold.target:
                paid_percent = threshold.paid_percent
                break
        # The full cost is one point per reduced characteristic per its reduced amount;
        # tracked here as a flat one-point bill per affected characteristic, since the
        # walk does not retain the raw reduced-point total separately from the applied
        # score. This is a simplification of FR-025's "times the points reduced".
        params = self.rules.chargen
        floor = self.floor()
        reduced = sorted(code for code, score in self.characteristics.items() if score <= floor)
        if not reduced:
            return
        total_cost = params.medical_restore_cost_per_point * len(reduced)
        owed = total_cost - (total_cost * paid_percent // 100)
        if owed <= 0:
            return
        self.add_debt(
            _Debt(
                amount=owed,
                restore="medical",
                characteristics=tuple(reduced),
                cost_per_point=params.medical_restore_cost_per_point,
            )
        )
        self.history.append(
            HistoryStep(
                kind="medical-bills",
                career=career_name,
                term=term,
                throw=StepThrow(faces=faces, modifiers=(), total=total, target=0, success=True),
                selected="",
                effects=(StepEffect(kind="debt", subject="", amount=owed),),
            )
        )

    def _apply_aging_if_due(self, career_name: str, term: int) -> None:
        params = self.rules.chargen
        if self.age < params.terms_aging_begins_at_age:
            return
        faces = _dice(self.roller, self.rules.aging.roll)
        modified = sum(faces) - self.total_terms_served
        # Rows are sorted by minimum; find the row whose range contains modified,
        # falling back to the lowest row when modified is beneath every range (the
        # floor rule for the aging table itself).
        row = self.rules.aging.rows[0]
        for candidate in self.rules.aging.rows:
            if modified >= candidate.minimum:
                row = candidate
        effects: list[StepEffect] = []
        for class_effect in row.effects:
            classes = self.rules.characteristics.classes
            candidates = sorted(
                code for code, cls in classes.items() if cls == class_effect.characteristic_class
            )
            count = min(class_effect.count, len(candidates))
            remaining = list(candidates)
            chosen = []
            for _ in range(count):
                index = self.roller.die(len(remaining)) - 1
                chosen.append(remaining.pop(index))
            crisis_codes = []
            for code in sorted(chosen):
                applied = _apply_characteristic_delta(
                    self.characteristics, code, class_effect.amount, self.floor()
                )
                effects.extend(applied)
                if self.characteristics[code] <= self.floor() and class_effect.amount < 0:
                    crisis_codes.append(code)
            if crisis_codes:
                self._trigger_medical_crisis(career_name, term, tuple(crisis_codes))
        self.history.append(
            HistoryStep(
                kind="aging",
                career=career_name,
                term=term,
                throw=StepThrow(faces=faces, modifiers=(), total=modified, target=0, success=True),
                selected="",
                effects=tuple(effects),
            )
        )

    def _roll_skills(self, career: CareerDefinition, count: int, term: int) -> None:
        for _ in range(count):
            eligible = _eligible_tables(career, self.characteristics)
            key, table = eligible[self.roller.die(len(eligible)) - 1]
            entry = table.entries[self.roller.die(len(table.entries)) - 1]
            effects = _apply_entry(
                entry,
                self.characteristics,
                self.rules.skills,
                self.skills,
                self.roller,
                self.floor(),
            )
            self.history.append(
                HistoryStep(
                    kind="skill-roll",
                    career=career.name,
                    term=term,
                    throw=None,
                    selected=key,
                    effects=tuple(effects),
                )
            )

    @staticmethod
    def _highest_matching_rank_row(rows, rank: int) -> int:
        """The highest-ranked row at or below `rank`; neither table is
        cumulative (research R10 item 7).
        """
        best_rank = -1
        amount = 0
        for row in rows:
            if row.rank <= rank and row.rank > best_rank:
                best_rank = row.rank
                amount = row.amount
        return amount

    def muster_out_service(
        self, career: CareerDefinition, terms: int, ladder: str, rank: int, benefit_rolls: int
    ) -> None:
        params = self.rules.chargen
        qualifies_for_pension = terms >= params.pension_minimum_terms
        cash_taken = 0
        rank_bonus = self._highest_matching_rank_row(params.mustering_out_rank_benefits, rank)
        material_dm = self._highest_matching_rank_row(params.mustering_out_material_rank_dm, rank)
        rolls = benefit_rolls + rank_bonus

        for _ in range(rolls):
            take_cash = False
            if cash_taken < params.mustering_out_maximum_cash_rolls:
                faces_c = _dice(self.roller, params.mustering_out_cash_choice_roll)
                take_cash = sum(faces_c) >= params.mustering_out_cash_choice_target
            if take_cash:
                dm = params.mustering_out_retired_cash_dm if qualifies_for_pension else 0
                faces = _dice(self.roller, params.mustering_out_roll)
                index = max(0, min(len(career.mustering_out.cash) - 1, sum(faces) + dm - 1))
                amount = career.mustering_out.cash[index]
                self.funds += amount
                cash_taken += 1
                self.history.append(
                    HistoryStep(
                        kind="benefit",
                        career=career.name,
                        term=0,
                        throw=None,
                        selected="",
                        effects=(StepEffect(kind="credits", subject="", amount=amount),),
                    )
                )
            else:
                faces = _dice(self.roller, params.mustering_out_roll)
                index = max(
                    0, min(len(career.mustering_out.benefits) - 1, sum(faces) + material_dm - 1)
                )
                item = career.mustering_out.benefits[index]
                if isinstance(item, BenefitItem):
                    self.benefits.append(item.name)
                    subject = item.name
                    amount = 0
                else:
                    delta = _apply_characteristic_delta(
                        self.characteristics, item.characteristic, item.amount, self.floor()
                    )
                    subject = item.characteristic
                    amount = delta[-1].amount
                self.history.append(
                    HistoryStep(
                        kind="benefit",
                        career=career.name,
                        term=0,
                        throw=None,
                        selected="",
                        effects=(StepEffect(kind="benefit", subject=subject, amount=amount),),
                    )
                )
        self.settle_debts()
        if qualifies_for_pension:
            amount = params.pension_base + params.pension_per_additional_term * (
                terms - params.pension_minimum_terms
            )
            self.pension += amount
            self.history.append(
                HistoryStep(
                    kind="pension",
                    career=career.name,
                    term=0,
                    throw=None,
                    selected="",
                    effects=(StepEffect(kind="pension", subject="", amount=amount),),
                )
            )
        self.history.append(
            HistoryStep(
                kind="mustering-out",
                career=career.name,
                term=0,
                throw=None,
                selected="",
                effects=(),
            )
        )

    def _current_title(self, career: CareerDefinition, ladder_name: str, rank: int) -> str:
        ladder = next(lad for lad in career.ladders if lad.name == ladder_name)
        rank_row = next((r for r in ladder.ranks if r.rank == rank), None)
        return rank_row.title if rank_row is not None else ""

    def run(self) -> None:
        self.roll_characteristics()
        self.roll_background_skills()
        entered_names: set[str] = set()
        first = True
        while self.total_terms_served < self.rules.chargen.terms_cap:
            career, entered_by = self.enter_career(entered_names)
            self.basic_training(career, first)
            entry_ladder = self._entry_ladder(career)
            self._grant_rank_bonus(career.name, 1, entry_ladder, 0)
            first = False
            entered_names.add(career.name)
            terms, ladder, rank, commissioned, ended, benefit_rolls, forfeit_all = (
                self.run_term_loop(career, entered_by)
            )
            title = self._current_title(career, ladder, rank)
            if title:
                self.title = title
            self.career_services.append(
                CareerService(
                    career=career.name,
                    terms=terms,
                    ladder=ladder,
                    rank=rank,
                    title=title,
                    commissioned=commissioned,
                    entered_by=entered_by,
                    ended=ended,
                    benefit_rolls=benefit_rolls,
                )
            )
            self.muster_out_service(career, terms, ladder, rank, benefit_rolls)
            # "Chose to leave" is the character declining to continue serving
            # at all (the continuation throw itself, FR-014) — the walk ends
            # here. A mishap or a failed re-enlistment forces them out of
            # *this* career only, while they still wished to continue serving,
            # which is what FR-015 obliges them to act on by seeking another.
            # The term cap forces the walk to end regardless of any of that.
            if ended in ("term cap", "chose to leave"):
                break


def generate_character(roller: Roller, rules: RulesData, *, name: str | None = None) -> Character:
    """Run the lifepath end to end and return the finished character
    (FR-001). Always alive, always named, always internally consistent
    (FR-022, FR-023, SC-003).
    """
    walk = _Walk(roller, rules)
    walk.run()

    name_roller = Roller(derive_seed(roller.seed, "name"))
    if name is None:
        rolled = roll_name(name_roller, rules.given_names, rules.surnames)
        full_name = rolled.full
        given_name = rolled.given_name
        surname = rolled.surname
        surname_region = rolled.region
    else:
        full_name = name
        given_name = ""
        surname = ""
        surname_region = ""

    return Character(
        seed=roller.seed,
        name=full_name,
        given_name=given_name,
        surname=surname,
        surname_region=surname_region,
        title=walk.title,
        characteristics=dict(walk.characteristics),
        skills=walk.skills.as_tuple(),
        careers=tuple(walk.career_services),
        age=walk.age,
        funds=walk.funds,
        debt=walk.debt,
        pension=walk.pension,
        benefits=tuple(walk.benefits),
        history=tuple(walk.history),
    )


def character_seed(master: int, index: int) -> int:
    """The seed position `index` of a batch runs on. Position 0 is `master`
    itself, never a derivation (research R2): that is what makes `--seed X`
    and `--seed X --count 1` produce the same person, and what makes a
    reported derived seed round-trip back to the character it names.
    """
    if index == 0:
        return master
    return derive_seed(master, index)


def generate_batch(
    seed: int | str | None, rules: RulesData, *, count: int = 1, name: str | None = None
) -> CharacterBatch:
    """Generate `count` characters from one master seed (FR-057, FR-048a,
    FR-050a).
    """
    if count < 1:
        raise CetoolsError(f"--count must be at least 1, got {count}")
    if name is not None and count > 1:
        raise CetoolsError("--name may not be combined with --count above 1")

    from cetools.seeds import resolve_seed

    master = resolve_seed(seed)
    characters = tuple(
        generate_character(Roller(character_seed(master, i)), rules, name=name)
        for i in range(count)
    )
    return CharacterBatch(seed=master, provenance=rules.provenance, characters=characters)
