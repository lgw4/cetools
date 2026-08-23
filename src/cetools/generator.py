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
from cetools.errors import CetoolsError, RulesDataError
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

_ENTERED_BY_SELECTED = "selected"
_ENTERED_BY_DRAFTED = "drafted"
_ENTERED_BY_FALLBACK = "fallback"


def _dice(roller: Roller, notation: str) -> tuple[tuple[int, ...], int]:
    """Throw `notation` and return its faces alongside the flat modifier it
    declares, so every call site honors a `dice = "2d6+N"` override rather
    than silently discarding it (T178) — the same modifier `task.roll`
    itemizes via `Modifier` (`tasks.py:126-127`).
    """
    count, sides, modifier = parse_notation(notation)
    return roller.dice(count, sides), modifier


def _roll_modifier(notation: str, modifier: int) -> list[Modifier]:
    """The `Modifier` list a nonzero dice-notation modifier contributes to a
    `StepThrow`, empty for the ordinary unmodified case.
    """
    return [Modifier(f"Roll ({notation})", modifier)] if modifier else []


def _table_row(file: str, rows: object, total: int):
    """Read `rows[total - 1]`, or raise `RulesDataError` naming `file`, the
    throw's total, and the table's row count when `total` falls outside it.

    The number of rows and the die a table declares are not required to
    agree; a mismatch is a data problem reported when it is read, not at
    load (contracts/data-files.md), so this is a runtime check rather than
    a cross-file rule in `rules.py`.
    """
    if total < 1 or total > len(rows):
        raise RulesDataError(
            f"{file}: a throw totaling {total} has no row at that position; "
            f"the table has {len(rows)} row(s)"
        )
    return rows[total - 1]


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
    actually applied when a floor clamp makes them differ — as two
    distinctly-kinded effects, `characteristic-called-for` and
    `characteristic`, so a reader of the record itself (not only a
    convention about their adjacency) can tell them apart (FR-030a, T165).
    """
    old = characteristics[code]
    called_for_value = old + delta
    applied_value = max(called_for_value, floor) if delta < 0 else called_for_value
    characteristics[code] = applied_value
    applied_delta = applied_value - old
    effects = [StepEffect(kind="characteristic", subject=code, amount=applied_delta)]
    if applied_delta != delta:
        effects.insert(0, StepEffect(kind="characteristic-called-for", subject=code, amount=delta))
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


def _parse_amount_with_faces(text: str, roller: Roller) -> tuple[int, tuple[int, ...]]:
    """A `MishapEffect.amount` field: dice notation or a signed integer,
    written as text either way (contracts/data-files.md). Dice notation may
    carry a leading sign — `"-1d6"` is a roll subtracted, not added
    (`parse_notation` itself admits no sign before the count). Returns the
    faces rolled alongside the amount, empty for a plain integer, which
    rolls nothing.
    """
    try:
        return int(text), ()
    except ValueError:
        pass
    sign = 1
    body = text
    if body and body[0] in "+-":
        sign = -1 if body[0] == "-" else 1
        body = body[1:]
    count, sides, modifier = parse_notation(body)
    faces = roller.dice(count, sides)
    return sign * (sum(faces) + modifier), faces


def _parse_amount(text: str, roller: Roller) -> int:
    amount, _faces = _parse_amount_with_faces(text, roller)
    return amount


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
    every covered characteristic to a fixed score; `medical` restores one
    point at `cost_per_point` each, to the characteristics named in
    `characteristics` — one entry per point owed, so a characteristic
    reduced by several points appears that many times — in the order the
    walk records (research/T143).

    `remainder` and `restored_count` (T157) carry a `medical` debt's
    progress across more than one partial settlement: a payment that alone
    is not enough for a full point must still count toward the next one
    that a later payment completes, and a characteristic already restored
    by an earlier settlement must not be restored again by a later one over
    the same debt.
    """

    __slots__ = (
        "amount",
        "restore",
        "characteristics",
        "restore_to",
        "cost_per_point",
        "remainder",
        "restored_count",
    )

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
        self.remainder = 0
        self.restored_count = 0


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
        self.cash_taken = 0

    def floor(self) -> int:
        return self.rules.characteristics.floor()

    def characteristic_dm(self, code: str | None) -> int:
        if code is None:
            return 0
        return self.rules.characteristics.characteristic_dm(self.characteristics[code])

    def settle_debts(self, career: str = "", term: int = 0) -> None:
        """Pay outstanding debts, oldest first, from `self.funds`, never
        taking funds below zero (FR-025a, FR-026). A debt that receives a
        payment this call records its own `debt-settled` step: the amount
        paid and which characteristics were restored and by how much, in
        the order they were considered, so funds and characteristics on
        the sheet replay from the history (FR-030, T144).
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
            effects: list[StepEffect] = [StepEffect(kind="debt", subject="", amount=payment)]
            if debt.restore == "crisis" and debt.amount == 0:
                for code in debt.characteristics:
                    old = self.characteristics[code]
                    new = max(old, debt.restore_to)
                    self.characteristics[code] = new
                    if new != old:
                        effects.append(
                            StepEffect(kind="characteristic", subject=code, amount=new - old)
                        )
            elif debt.restore == "medical" and debt.cost_per_point > 0:
                # A payment too small for a full point still counts toward
                # the next one a later settlement of this same debt
                # completes, and a characteristic already restored is
                # never restored again (T157).
                debt.remainder += payment
                new_points = debt.remainder // debt.cost_per_point
                debt.remainder -= new_points * debt.cost_per_point
                start = debt.restored_count
                candidates = sorted(debt.characteristics)[start : start + new_points]
                for code in candidates:
                    self.characteristics[code] += 1
                    effects.append(StepEffect(kind="characteristic", subject=code, amount=1))
                debt.restored_count += len(candidates)
            self.history.append(
                HistoryStep(
                    kind="debt-settled",
                    career=career,
                    term=term,
                    throw=None,
                    selected="",
                    effects=tuple(effects),
                )
            )
            if debt.amount > 0:
                remaining.append(debt)
        self.debts = remaining

    def add_debt(self, debt: _Debt, career: str = "", term: int = 0) -> None:
        self.debt += debt.amount
        self.debts.append(debt)
        self.settle_debts(career, term)

    def roll_characteristics(self) -> None:
        effects = []
        all_faces: list[int] = []
        notation = self.rules.chargen.characteristics_roll
        for code in self.rules.characteristics.names:
            faces, modifier = _dice(self.roller, notation)
            all_faces.extend(faces)
            score = sum(faces) + modifier
            self.characteristics[code] = score
            effects.append(StepEffect(kind="characteristic", subject=code, amount=score))
        self.history.append(
            HistoryStep(
                kind="characteristics",
                career="",
                term=0,
                throw=StepThrow(
                    faces=tuple(all_faces),
                    modifiers=(),
                    total=sum(all_faces),
                    target=0,
                    success=True,
                ),
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
        faces: list[int] = []
        for i in range(count):
            pool = homeworld if i < homeworld_count else education
            pick = self.roller.die(len(pool))
            faces.append(pick)
            grant = pool[pick - 1]
            resolved = _resolve_specialty(grant.skill, self.rules.skills, self.roller)
            level = self.skills.apply_explicit(resolved, grant.level)
            effects.append(StepEffect(kind="skill", subject=_skill_label(resolved), amount=level))
        self.history.append(
            HistoryStep(
                kind="background-skills",
                career="",
                term=0,
                throw=StepThrow(
                    faces=tuple(faces), modifiers=(), total=sum(faces), target=0, success=True
                ),
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
        faces, roll_modifier = _dice(self.roller, throw.dice)
        modifiers = _roll_modifier(throw.dice, roll_modifier)
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
        faces, modifier = _dice(self.roller, draft.roll)
        row = sum(faces) + modifier
        name = _table_row("draft.toml", draft.careers, row)
        self.history.append(
            HistoryStep(
                kind="draft",
                career="",
                term=0,
                throw=StepThrow(
                    faces=faces,
                    modifiers=tuple(_roll_modifier(draft.roll, modifier)),
                    total=row,
                    target=0,
                    success=True,
                ),
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
                # collision with either route falls through to a re-enterable
                # career instead, which every shipped ruleset guarantees
                # exists. The substitution is its own step (FR-015a), distinct
                # from the "draft" step, which still names the career the
                # draft table actually resolved to (T189) — naming the
                # *substitute* here, not the collided-with career the "draft"
                # step already names, or the step restates what came before
                # it and leaves the substitute unexplained (T201).
                substitute = next(c for c in self.rules.careers.values() if c.re_enterable)
                self.history.append(
                    HistoryStep(
                        kind="career-selected",
                        career="",
                        term=0,
                        throw=None,
                        selected=substitute.name,
                        effects=(),
                    )
                )
                candidate = substitute
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
        faces: tuple[int, ...] = ()
        if is_first_career and params.basic_training_first_career_all:
            # No die is rolled: every entry of the table is granted, so this
            # step decided rather than threw (data-model.md).
            entries = service_table.entries
        else:
            count = params.basic_training_subsequent_career_count
            drawn = [self.roller.die(len(service_table.entries)) for _ in range(count)]
            faces = tuple(drawn)
            entries = [service_table.entries[pick - 1] for pick in drawn]
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
        throw = (
            StepThrow(faces=faces, modifiers=(), total=sum(faces), target=0, success=True)
            if faces
            else None
        )
        self.history.append(
            HistoryStep(
                kind="basic-training",
                career=career.name,
                term=1,
                throw=throw,
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
            survival = career.throws["survival"]
            faces, roll_modifier = _dice(self.roller, survival.dice)
            dice_total = sum(faces)
            char_dm = self.characteristic_dm(survival.characteristic)
            modifiers = _roll_modifier(survival.dice, roll_modifier)
            if survival.characteristic is not None:
                modifiers.append(
                    Modifier(
                        f"Characteristic {self.characteristics[survival.characteristic]}", char_dm
                    )
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
                mishap_faces, mishap_modifier = _dice(self.roller, self.rules.mishaps.roll)
                mishap_total = sum(mishap_faces) + mishap_modifier
                row = _table_row("mishaps.toml", self.rules.mishaps.rows, mishap_total)
                self.history.append(
                    HistoryStep(
                        kind="mishap",
                        career=career.name,
                        term=term,
                        throw=StepThrow(
                            faces=mishap_faces,
                            modifiers=tuple(
                                _roll_modifier(self.rules.mishaps.roll, mishap_modifier)
                            ),
                            total=mishap_total,
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
                        # Billed exactly the way an injury's own reduction
                        # is (T143, T150): FR-024's reduction persists
                        # "unless the character's medical bills are paid",
                        # which presupposes a bill exists to pay (T162).
                        reduced = self._apply_class_effect(effect, career.name, term)
                        if reduced:
                            self._raise_medical_bill(career.name, term, current_rank, reduced)
                    elif effect.kind == "debt":
                        amount = _parse_amount(effect.amount, self.roller)
                        # Recorded before `add_debt`, which settles
                        # immediately: the step that creates a debt must
                        # precede the settlement it can trigger (T164).
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
                        self.add_debt(_Debt(amount=amount, restore="none"), career.name, term)
                    elif effect.kind == "years":
                        extra_years += _parse_amount(effect.amount, self.roller)
                    elif effect.kind == "forfeit-career-benefits":
                        forfeit_all = True
                    elif effect.kind == "roll-injury":
                        self._roll_injury(career.name, term, current_rank)
                terms += 1
                # Every mishap-ended term forfeits its own benefit roll
                # unconditionally (FR-020); this is the only place that
                # happens (T145).
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
                faces_c, roll_mod_c = _dice(self.roller, throw.dice)
                char_dm_c = self.characteristic_dm(throw.characteristic)
                mods_c = _roll_modifier(throw.dice, roll_mod_c)
                if throw.characteristic is not None:
                    mods_c.append(
                        Modifier(
                            f"Characteristic {self.characteristics[throw.characteristic]}",
                            char_dm_c,
                        )
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
                # Attempted whenever the career offers the throw (FR-008),
                # not only when a higher rank exists to move to — no data
                # declares that precondition. A success still grants the
                # skill roll FR-009 requires even where the ladder has
                # nothing above the current rank; only the rank move and
                # its bonus are conditioned on `ranks_above` (T169).
                current_ladder = next(
                    ladder for ladder in career.ladders if ladder.name == current_ladder_name
                )
                ranks_above = sorted(r.rank for r in current_ladder.ranks if r.rank > current_rank)
                throw = career.throws["promotion"]
                faces_p, roll_mod_p = _dice(self.roller, throw.dice)
                char_dm_p = self.characteristic_dm(throw.characteristic)
                mods_p = _roll_modifier(throw.dice, roll_mod_p)
                if throw.characteristic is not None:
                    mods_p.append(
                        Modifier(
                            f"Characteristic {self.characteristics[throw.characteristic]}",
                            char_dm_p,
                        )
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
                    extra_rolls += params.skill_rolls_on_advancement
                    if ranks_above:
                        current_rank = ranks_above[0]
                        self._grant_rank_bonus(career.name, term, current_ladder, current_rank)

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
            faces_k, continuation_modifier = _dice(self.roller, continuation)
            total_k = sum(faces_k) + continuation_modifier
            wants_to_continue = total_k >= params.continuation_target
            self.history.append(
                HistoryStep(
                    kind="continuation",
                    career=career.name,
                    term=term,
                    throw=StepThrow(
                        faces=faces_k,
                        modifiers=tuple(_roll_modifier(continuation, continuation_modifier)),
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
            faces_r, roll_mod_r = _dice(self.roller, re_enlist.dice)
            mods_r = _roll_modifier(re_enlist.dice, roll_mod_r)
            if re_enlist.characteristic is not None:
                mods_r.append(
                    Modifier(
                        f"Characteristic {self.characteristics[re_enlist.characteristic]}",
                        self.characteristic_dm(re_enlist.characteristic),
                    )
                )
            total_r = sum(faces_r) + sum(m.value for m in mods_r)
            success_r = total_r >= re_enlist.target
            self.history.append(
                HistoryStep(
                    kind="re-enlistment",
                    career=career.name,
                    term=term,
                    throw=StepThrow(
                        faces=faces_r,
                        modifiers=tuple(mods_r),
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
        benefit_rolls = (
            0 if forfeit_all else params.mustering_out_per_term * max(0, terms - forfeited_terms)
        )
        return (
            terms,
            current_ladder_name,
            current_rank,
            commissioned,
            ended,
            benefit_rolls,
            forfeit_all,
        )

    def _apply_class_effect(
        self, effect, career_name: str, term: int, kind: str = "mishap"
    ) -> dict[str, int]:
        """Apply the effect and return the magnitude of each characteristic
        it actually reduced (research R13's applied amount, never the
        called-for one), keyed by code. Empty for a characteristic already
        at the floor and chosen again, which applies a delta of zero
        (T146). The caller decides what the reduction is worth — the term
        loop's direct mishap effects ignore it, `_roll_injury` accumulates
        it into a medical bill (T143).

        `kind` names which step this reduction is recorded under (FR-030a):
        `"mishap"` for the term loop's own direct effects, the default, or
        `"injury"` when `_roll_injury` is the caller — an injury's
        reduction is otherwise indistinguishable from a mishap row's own
        (T174).

        Never raises a medical crisis, even when a reduction floors a
        characteristic: FR-021 defines a crisis as arising from an *aging*
        effect specifically, and this method also serves the term loop's
        direct mishap effects and `_roll_injury`, neither of which is aging
        (T160). `_apply_aging_if_due` applies its own class effects and
        raises its own crisis, independently of this method.
        """
        classes = self.rules.characteristics.classes
        candidates = sorted(
            code for code, cls in classes.items() if cls == effect.characteristic_class
        )
        count = min(effect.count, len(candidates))
        chosen: list[str] = []
        remaining = list(candidates)
        choice_faces: list[int] = []
        for _ in range(count):
            pick = self.roller.die(len(remaining))
            choice_faces.append(pick)
            chosen.append(remaining.pop(pick - 1))
        amount, amount_faces = _parse_amount_with_faces(effect.amount, self.roller)
        effects: list[StepEffect] = []
        reduced: dict[str, int] = {}
        for code in sorted(chosen):
            applied = _apply_characteristic_delta(self.characteristics, code, amount, self.floor())
            effects.extend(applied)
            applied_delta = applied[-1].amount
            if applied_delta < 0:
                reduced[code] = -applied_delta
        faces = tuple(choice_faces) + tuple(amount_faces)
        throw = (
            StepThrow(faces=faces, modifiers=(), total=sum(faces), target=0, success=True)
            if faces
            else None
        )
        self.history.append(
            HistoryStep(
                kind=kind,
                career=career_name,
                term=term,
                throw=throw,
                selected="",
                effects=tuple(effects),
            )
        )
        return reduced

    def _trigger_medical_crisis(self, career_name: str, term: int, codes: tuple[str, ...]) -> None:
        params = self.rules.chargen
        faces, roll_modifier = _dice(self.roller, params.medical_crisis_roll)
        total = sum(faces) + roll_modifier
        amount = total * params.medical_crisis_multiplier
        # Recorded before `add_debt`, which settles immediately: the step
        # that creates a debt must precede the settlement it can trigger
        # (T164).
        self.history.append(
            HistoryStep(
                # A crisis debt is *created* here, not settled — that is
                # `settle_debts`'s own step, which this name is reserved
                # for once it actually records settlement (T144).
                kind="medical-crisis",
                career=career_name,
                term=term,
                throw=StepThrow(
                    faces=faces,
                    modifiers=tuple(_roll_modifier(params.medical_crisis_roll, roll_modifier)),
                    total=total,
                    target=0,
                    success=True,
                ),
                selected="",
                effects=(StepEffect(kind="debt", subject="", amount=amount),),
            )
        )
        self.add_debt(
            _Debt(
                amount=amount,
                restore="crisis",
                characteristics=codes,
                restore_to=params.medical_crisis_restores_to,
            ),
            career_name,
            term,
        )

    def _roll_injury(self, career_name: str, term: int, rank: int) -> None:
        faces, modifier = _dice(self.roller, self.rules.mishaps.injury_roll)
        total = sum(faces) + modifier
        row = _table_row("mishaps.toml", self.rules.mishaps.injuries, total)
        self.history.append(
            HistoryStep(
                kind="injury",
                career=career_name,
                term=term,
                throw=StepThrow(
                    faces=faces,
                    modifiers=tuple(_roll_modifier(self.rules.mishaps.injury_roll, modifier)),
                    total=total,
                    target=0,
                    success=True,
                ),
                selected=row.description,
                effects=(),
            )
        )
        reduced: dict[str, int] = {}
        for effect in row.effects:
            if effect.kind == "characteristic-class":
                effect_reduced = self._apply_class_effect(effect, career_name, term, kind="injury")
                for code, amount in effect_reduced.items():
                    reduced[code] = reduced.get(code, 0) + amount
        if reduced:
            self._raise_medical_bill(career_name, term, rank, reduced)

    def _raise_medical_bill(
        self, career_name: str, term: int, rank: int, reduced: dict[str, int]
    ) -> None:
        career = next(c for c in self.rules.careers.values() if c.name == career_name)
        tier = self.rules.medical_tiers.tiers[career.medical_tier]
        faces, roll_modifier = _dice(self.roller, self.rules.medical_tiers.roll)
        rank_bonus = rank if self.rules.medical_tiers.rank_dm else 0
        total = sum(faces) + roll_modifier + rank_bonus
        paid_percent = 0
        for threshold in tier:
            if total >= threshold.target:
                paid_percent = threshold.paid_percent
                break
        # The bill is the per-point cost times the points actually reduced
        # by this injury, never the number of characteristics currently
        # sitting at the floor: an injury that reduces a score without
        # flooring it still owes for the points it took, and an
        # aging-floored characteristic is never billed to the employer for
        # an injury it played no part in (T143). One entry of
        # `characteristics` per point owed, so `settle_debts` restores
        # exactly the points this bill covers.
        params = self.rules.chargen
        total_points = sum(reduced.values())
        if total_points <= 0:
            return
        total_cost = params.medical_restore_cost_per_point * total_points
        owed = total_cost - (total_cost * paid_percent // 100)
        characteristics = tuple(
            sorted(code for code, points in reduced.items() for _ in range(points))
        )
        throw = StepThrow(
            faces=faces,
            modifiers=tuple(_roll_modifier(self.rules.medical_tiers.roll, roll_modifier)),
            total=total,
            target=0,
            success=True,
        )
        if owed <= 0:
            # The employer's share covers the bill in full: there is no
            # debt to settle later, so the points are restored immediately
            # rather than left permanently reduced, and the tier throw that
            # already happened is still recorded (T161). One effect per
            # characteristic, its whole restored amount at once — not one
            # per point as `settle_debts` records across possibly several
            # partial payments — since a single, one-shot restoration has
            # no partial progress for the per-point form to track.
            effects = []
            for code, points in reduced.items():
                self.characteristics[code] += points
                effects.append(StepEffect(kind="characteristic", subject=code, amount=points))
            self.history.append(
                HistoryStep(
                    kind="medical-bills",
                    career=career_name,
                    term=term,
                    throw=throw,
                    selected="",
                    effects=tuple(effects),
                )
            )
            return
        # Recorded before `add_debt`, which settles immediately: the step
        # that creates a debt must precede the settlement it can trigger
        # (T164).
        self.history.append(
            HistoryStep(
                kind="medical-bills",
                career=career_name,
                term=term,
                throw=throw,
                selected="",
                effects=(StepEffect(kind="debt", subject="", amount=owed),),
            )
        )
        self.add_debt(
            _Debt(
                amount=owed,
                restore="medical",
                characteristics=characteristics,
                # The debt's own per-point price, not the flat undiscounted
                # rate: `owed` is already the character's share of
                # `total_cost`, so a per-point price built from the full
                # rate demanded more per point than the bill actually
                # charged, and a full payment of a discounted bill restored
                # nothing (T161). `max(1, ...)` keeps this from dividing by
                # zero on a share smaller than one credit per point, an
                # edge case no shipped data reaches.
                cost_per_point=max(1, owed // total_points),
            ),
            career_name,
            term,
        )

    def _apply_aging_if_due(self, career_name: str, term: int) -> None:
        params = self.rules.chargen
        if self.age < params.terms_aging_begins_at_age:
            return
        faces, roll_modifier = _dice(self.roller, self.rules.aging.roll)
        modified = sum(faces) + roll_modifier - self.total_terms_served
        # Rows are sorted by minimum. The lowest row is a floor: a modified
        # result below it reads that row too (contracts/data-files.md).
        # Above the floor, a result must fall within some row's declared
        # `minimum`-`maximum` range; the range is honored on both ends
        # rather than matched on `minimum` alone, or a gap between two
        # bounded rows would silently read whichever row sorts highest
        # below it (T186).
        rows = self.rules.aging.rows
        if modified < rows[0].minimum:
            row = rows[0]
        else:
            row = next(
                (
                    candidate
                    for candidate in rows
                    if candidate.minimum <= modified
                    and (candidate.maximum is None or modified <= candidate.maximum)
                ),
                None,
            )
            if row is None:
                raise RulesDataError(
                    f"aging.toml: a throw modified to {modified} falls in a gap no row covers"
                )
        effects: list[StepEffect] = []
        # Every crisis this row's effects raise is deferred to after the
        # `aging` step below is appended (T163): the step that caused a
        # crisis must precede it in the history, and this step isn't
        # complete — its own `effects` aren't finished accumulating — until
        # every one of the row's class effects has been applied. One tuple
        # of codes per class effect that reached the floor, preserving the
        # existing one-crisis-per-class-effect shape (a row naming both a
        # physical and a mental class effect that each float a
        # characteristic to the floor still raises two crisis debts, not
        # one merged one).
        pending_crises: list[tuple[str, ...]] = []
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
                # See the identical comment in `_apply_class_effect` (T146):
                # trigger only where this reduction actually applied.
                applied_delta = applied[-1].amount
                if applied_delta < 0 and self.characteristics[code] <= self.floor():
                    crisis_codes.append(code)
            if crisis_codes:
                pending_crises.append(tuple(crisis_codes))
        self.history.append(
            HistoryStep(
                kind="aging",
                career=career_name,
                term=term,
                throw=StepThrow(
                    faces=faces,
                    modifiers=tuple(_roll_modifier(self.rules.aging.roll, roll_modifier)),
                    total=modified,
                    target=0,
                    success=True,
                ),
                selected="",
                effects=tuple(effects),
            )
        )
        for codes in pending_crises:
            self._trigger_medical_crisis(career_name, term, codes)

    def _roll_skills(self, career: CareerDefinition, count: int, term: int) -> None:
        for _ in range(count):
            eligible = _eligible_tables(career, self.characteristics)
            table_pick = self.roller.die(len(eligible))
            key, table = eligible[table_pick - 1]
            entry_pick = self.roller.die(len(table.entries))
            entry = table.entries[entry_pick - 1]
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
                    throw=StepThrow(
                        faces=(table_pick, entry_pick),
                        modifiers=(),
                        total=table_pick + entry_pick,
                        target=0,
                        success=True,
                    ),
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
        self,
        career: CareerDefinition,
        terms: int,
        ladder: str,
        rank: int,
        benefit_rolls: int,
        forfeit_all: bool = False,
    ) -> int:
        """Roll every benefit this service earns, and return the count
        actually rolled — the term-derived `benefit_rolls` plus the
        rank-derived bonus, `0` when `forfeit_all` — for the caller to
        record on `CareerService.benefit_rolls` (T188).
        """
        params = self.rules.chargen
        qualifies_for_pension = terms >= params.pension_minimum_terms
        rank_bonus = self._highest_matching_rank_row(params.mustering_out_rank_benefits, rank)
        material_dm = self._highest_matching_rank_row(params.mustering_out_material_rank_dm, rank)
        # A mishap's `forfeit-career-benefits` effect forfeits every roll
        # this service would otherwise take, not merely the term-count
        # half of it: `benefit_rolls` was already zeroed for it, but the
        # rank-derived bonus rolls were still added on top, so a character
        # dishonorably discharged or imprisoned at a high rank still took
        # one to three rolls from a service that recorded taking none
        # (T168).
        rolls = 0 if forfeit_all else benefit_rolls + rank_bonus

        for _ in range(rolls):
            take_cash = False
            faces_c: tuple[int, ...] = ()
            cash_choice_modifier = 0
            # `self.cash_taken` is a whole-character count (FR-016): "how
            # many of a character's rolls" are cash, not how many of one
            # career service's are, so it is never reset per service (T147).
            if self.cash_taken < params.mustering_out_maximum_cash_rolls:
                faces_c, cash_choice_modifier = _dice(
                    self.roller, params.mustering_out_cash_choice_roll
                )
                take_cash = (
                    sum(faces_c) + cash_choice_modifier >= params.mustering_out_cash_choice_target
                )
            cash_choice_modifiers = _roll_modifier(
                params.mustering_out_cash_choice_roll, cash_choice_modifier
            )
            if take_cash:
                dm = params.mustering_out_retired_cash_dm if qualifies_for_pension else 0
                faces, roll_modifier = _dice(self.roller, params.mustering_out_roll)
                amount = _table_row(
                    f"{career.name}: mustering-out.cash",
                    career.mustering_out.cash,
                    sum(faces) + roll_modifier + dm,
                )
                self.funds += amount
                self.cash_taken += 1
                all_faces = faces_c + faces
                modifiers = tuple(
                    cash_choice_modifiers
                    + _roll_modifier(params.mustering_out_roll, roll_modifier)
                )
                self.history.append(
                    HistoryStep(
                        kind="benefit",
                        career=career.name,
                        term=0,
                        throw=StepThrow(
                            faces=all_faces,
                            modifiers=modifiers,
                            total=sum(all_faces) + sum(m.value for m in modifiers),
                            target=0,
                            success=True,
                        ),
                        selected="",
                        effects=(StepEffect(kind="credits", subject="", amount=amount),),
                    )
                )
            else:
                faces, roll_modifier = _dice(self.roller, params.mustering_out_roll)
                item = _table_row(
                    f"{career.name}: mustering-out.benefits",
                    career.mustering_out.benefits,
                    sum(faces) + roll_modifier + material_dm,
                )
                if isinstance(item, BenefitItem):
                    self.benefits.append(item.name)
                    effects: tuple[StepEffect, ...] = (
                        StepEffect(kind="benefit", subject=item.name, amount=0),
                    )
                else:
                    # `_apply_characteristic_delta` already returns
                    # correctly-kinded `characteristic` effects, including
                    # the called-for/applied pair a floor clamp produces
                    # (research R13) — used directly, not rewrapped as a
                    # scalar `benefit` effect that hid this from anything
                    # grouping by `characteristic` (SC-005).
                    effects = tuple(
                        _apply_characteristic_delta(
                            self.characteristics, item.characteristic, item.amount, self.floor()
                        )
                    )
                all_faces = faces_c + faces
                modifiers = tuple(
                    cash_choice_modifiers
                    + _roll_modifier(params.mustering_out_roll, roll_modifier)
                )
                self.history.append(
                    HistoryStep(
                        kind="benefit",
                        career=career.name,
                        term=0,
                        throw=StepThrow(
                            faces=all_faces,
                            modifiers=modifiers,
                            total=sum(all_faces) + sum(m.value for m in modifiers),
                            target=0,
                            success=True,
                        ),
                        selected="",
                        effects=effects,
                    )
                )
        self.settle_debts(career.name, 0)
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
        return rolls

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
            rolls_taken = self.muster_out_service(
                career, terms, ladder, rank, benefit_rolls, forfeit_all
            )
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
                    benefit_rolls=rolls_taken,
                )
            )
            # "Chose to leave" is the character declining to continue serving
            # at all (the continuation throw itself, FR-014) — the walk ends
            # here. A mishap or a failed re-enlistment forces them out of
            # *this* career only, while they still wished to continue serving,
            # which is what FR-015 obliges them to act on by seeking another.
            # The term cap forces the walk to end regardless of any of that.
            if ended in ("term cap", "chose to leave"):
                break


def _validate_name(name: str | None) -> None:
    """FR-047 requires a supplied name verbatim; a name that cannot be
    rendered verbatim is refused instead (FR-053c). Empty or
    whitespace-only leaves a dangling title separator (T148); a tab puts a
    third tab on a line FR-046 requires to hold exactly two, and a newline
    writes a blank line inside a sheet, which FR-048a reserves as the
    separator between sheets in a batch (T170).
    """
    if name is None:
        return
    if not name.strip():
        raise CetoolsError("name must not be empty or whitespace-only")
    if "\t" in name or "\n" in name:
        raise CetoolsError("name must not contain a tab or a newline")


def generate_character(roller: Roller, rules: RulesData, *, name: str | None = None) -> Character:
    """Run the lifepath end to end and return the finished character
    (FR-001). Always alive, always named, always internally consistent
    (FR-022, FR-023, SC-003).
    """
    _validate_name(name)
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
        characteristic_symbols=tuple(
            rules.characteristics.symbol(score) for score in walk.characteristics.values()
        ),
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
    _validate_name(name)

    from cetools.seeds import resolve_seed

    master = resolve_seed(seed)
    characters = tuple(
        generate_character(Roller(character_seed(master, i)), rules, name=name)
        for i in range(count)
    )
    return CharacterBatch(seed=master, provenance=rules.provenance, characters=characters)
