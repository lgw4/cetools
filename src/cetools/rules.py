"""Discovery, composition, and validation of the whole rules data set
(contracts/data-files.md, data-model.md).

Validation is a function, not a control flow: `_validate` composes the
packaged data set with an optional override, checks every file, and returns
a `RulesData` (if the whole set is clean) alongside a `ValidationReport`.
`load_rules` and `validate_rules` call it and differ only in what they do
with the result (research R7).
"""

import re
import tomllib
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from importlib import resources
from pathlib import Path
from types import MappingProxyType

from cetools.careers import CareerDefinition
from cetools.careers import parse_career as _parse_career
from cetools.errors import RulesDataError, ValidationProblem, type_name
from cetools.provenance import (
    Disposition,
    FileProvenance,
    Provenance,
    fingerprint,
    package_version,
)
from cetools.registries import (
    BenefitRegistry,
    CharacteristicRegistry,
    SkillRegistry,
    parse_benefits,
    parse_characteristics,
    parse_skills,
)
from cetools.tasks import Band, TaskParameters, _check_dice

_HEADER_KEYS = frozenset({"schema", "schema-version"})
_BAND_RANGE = re.compile(r"^(\d+)-(\d+)$")
_BAND_UNBOUNDED = re.compile(r"^(\d+)\+$")

_SUPPORTED_VERSION = {
    "task-parameters": 1,
    "characteristics": 1,
    "skills": 1,
    "benefits": 1,
    "career": 1,
}
_SINGLETON_KINDS = ("task-parameters", "characteristics", "skills", "benefits")
_CANONICAL_FILE = {
    "task-parameters": "tasks.toml",
    "characteristics": "characteristics.toml",
    "skills": "skills.toml",
    "benefits": "benefits.toml",
}
_KIND_AT_CANONICAL_FILE = {file: kind for kind, file in _CANONICAL_FILE.items()}


@dataclass(frozen=True, slots=True)
class RulesData:
    """The loaded, fully validated rules data set (data-model.md)."""

    task_parameters: TaskParameters
    characteristics: CharacteristicRegistry
    skills: SkillRegistry
    benefits: BenefitRegistry
    careers: Mapping[str, CareerDefinition]
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Every problem found composing and checking a data set, plus its
    provenance, known even when validation fails because composition
    precedes validation.
    """

    provenance: Provenance
    file_count: int
    problems: tuple[ValidationProblem, ...]

    @property
    def valid(self) -> bool:
        return not self.problems


# --- task-parameters schema (contracts/data-files.md) ----------------------


def _unrecognized_key_problems(
    data: Mapping[str, object], allowed: frozenset[str], file: str, prefix: str = ""
) -> list[ValidationProblem]:
    extra = sorted(set(data) - allowed)
    return [
        ValidationProblem(
            file=file,
            location=f"{prefix}{key}",
            found=f"unrecognized key {key!r}",
            expected=f"one of: {', '.join(sorted(allowed))}",
        )
        for key in extra
    ]


def parse_task_parameters(
    data: Mapping[str, object], file: str
) -> tuple[TaskParameters | None, tuple[ValidationProblem, ...]]:
    """Validate one already-parsed `task-parameters` TOML dict, collecting
    every problem rather than raising on the first (research R7). Restates
    every rule the previous single-purpose reader enforced.
    """
    problems: list[ValidationProblem] = []
    problems.extend(
        _unrecognized_key_problems(
            data, _HEADER_KEYS | {"task", "difficulty-dms", "characteristic-dms"}, file
        )
    )

    task = data.get("task")
    if not isinstance(task, dict):
        problems.append(
            ValidationProblem(
                file=file,
                location="task",
                found="missing" if task is None else type_name(task),
                expected="a [task] table",
            )
        )
        task = {}
    else:
        problems.extend(
            _unrecognized_key_problems(task, {"roll", "target", "unskilled-dm"}, file, "task.")
        )

    roll: str | None = None
    if "roll" not in task:
        problems.append(
            ValidationProblem(
                file=file, location="task.roll", found="missing", expected="a string"
            )
        )
    elif not isinstance(task["roll"], str):
        problems.append(
            ValidationProblem(
                file=file,
                location="task.roll",
                found=type_name(task["roll"]),
                expected="a string",
            )
        )
    else:
        try:
            _check_dice(task["roll"])
            roll = task["roll"]
        except RulesDataError as exc:
            problems.append(
                ValidationProblem(
                    file=file, location="task.roll", found=repr(task["roll"]), expected=str(exc)
                )
            )

    target = _require_int(task, "target", file, "task.target", problems)
    unskilled_dm = _require_int(task, "unskilled-dm", file, "task.unskilled-dm", problems)

    difficulty_dms: dict[str, int] = {}
    dd = data.get("difficulty-dms")
    if not isinstance(dd, dict) or not dd:
        problems.append(
            ValidationProblem(
                file=file,
                location="difficulty-dms",
                found=(
                    "missing" if dd is None else ("an empty table" if dd == {} else type_name(dd))
                ),
                expected="a [difficulty-dms] table with at least one entry",
            )
        )
    else:
        zero_count = 0
        ok = True
        for name, value in dd.items():
            if not isinstance(value, int) or isinstance(value, bool):
                problems.append(
                    ValidationProblem(
                        file=file,
                        location=f"difficulty-dms.{name}",
                        found=type_name(value),
                        expected="an integer",
                    )
                )
                ok = False
                continue
            if value == 0:
                zero_count += 1
            difficulty_dms[name] = value
        if ok and zero_count != 1:
            problems.append(
                ValidationProblem(
                    file=file,
                    location="difficulty-dms",
                    found=f"{zero_count} rungs at modifier 0",
                    expected="exactly one rung at modifier 0",
                )
            )

    bands: list[Band] = []
    cd = data.get("characteristic-dms")
    if not isinstance(cd, dict) or not cd:
        problems.append(
            ValidationProblem(
                file=file,
                location="characteristic-dms",
                found=(
                    "missing" if cd is None else ("an empty table" if cd == {} else type_name(cd))
                ),
                expected="a [characteristic-dms] table with at least one entry",
            )
        )
    else:
        unbounded_count = 0
        ok = True
        for key, value in cd.items():
            if not isinstance(value, int) or isinstance(value, bool):
                problems.append(
                    ValidationProblem(
                        file=file,
                        location=f"characteristic-dms.{key}",
                        found=type_name(value),
                        expected="an integer",
                    )
                )
                ok = False
                continue
            range_match = _BAND_RANGE.match(key)
            unbounded_match = _BAND_UNBOUNDED.match(key)
            if range_match:
                minimum, maximum = int(range_match.group(1)), int(range_match.group(2))
            elif unbounded_match:
                minimum, maximum = int(unbounded_match.group(1)), None
                unbounded_count += 1
            else:
                problems.append(
                    ValidationProblem(
                        file=file,
                        location=f"characteristic-dms.{key}",
                        found=repr(key),
                        expected="a key of the form N-M or N+",
                    )
                )
                ok = False
                continue
            bands.append(Band(minimum=minimum, maximum=maximum, dm=value))
        if ok and unbounded_count != 1:
            problems.append(
                ValidationProblem(
                    file=file,
                    location="characteristic-dms",
                    found=f"{unbounded_count} unbounded bands",
                    expected="exactly one unbounded band",
                )
            )
    bands.sort(key=lambda band: band.minimum)

    if problems:
        return None, tuple(problems)
    return (
        TaskParameters(
            roll=roll,
            target=target,
            unskilled_dm=unskilled_dm,
            difficulty_dms=difficulty_dms,
            characteristic_bands=tuple(bands),
        ),
        (),
    )


def _require_int(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> int | None:
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="an integer")
        )
        return None
    value = container[key]
    if not isinstance(value, int) or isinstance(value, bool):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="an integer"
            )
        )
        return None
    return value


# --- discovery ---------------------------------------------------------------


def _walk_toml(traversable):
    for entry in sorted(traversable.iterdir(), key=lambda t: t.name):
        if entry.is_dir():
            yield from _walk_toml(entry)
        elif entry.name.endswith(".toml"):
            yield entry


def _unreadable(file: str, exc: OSError) -> ValidationProblem:
    """A file that is present but cannot be read is a problem about the file
    as a whole, so it carries no location (FR-020a, FR-022). It contributes
    no content and the remaining files are still checked.
    """
    return ValidationProblem(
        file=file,
        found=f"a file that could not be read: {exc.strerror or exc}",
        expected="a readable file",
    )


def _discover_packaged() -> tuple[dict[str, bytes], tuple[ValidationProblem, ...]]:
    root = resources.files("cetools.data")
    files: dict[str, bytes] = {}
    problems: list[ValidationProblem] = []
    for entry in _walk_toml(root):
        try:
            files[entry.name] = entry.read_bytes()
        except OSError as exc:
            problems.append(_unreadable(entry.name, exc))
    return files, tuple(problems)


def _packaged_kind_map(packaged: dict[str, bytes]) -> dict[str, str]:
    kinds: dict[str, str] = {}
    for basename, data in packaged.items():
        try:
            parsed = tomllib.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        kind = parsed.get("schema")
        if isinstance(kind, str) and kind in _SUPPORTED_VERSION:
            kinds[basename] = kind
    return kinds


# --- composition ---------------------------------------------------------------


def _unlistable(name: str, exc: OSError) -> ValidationProblem:
    """A directory that is present but cannot be listed, reported the way an
    unreadable file is (FR-020a, FR-022).

    Passing it over instead would leave every house rule beneath it silently
    out of force while the run reported `packaged` and exited 0, which is the
    failure FR-028 exists to remove — and is exactly the treatment
    `_collect_entry` below refuses to give a single unreadable file.
    """
    return ValidationProblem(
        file=name,
        found=f"a directory that could not be listed: {exc.strerror or exc}",
        expected="a readable directory",
    )


def _not_a_regular_file(basename: str) -> ValidationProblem:
    """A FIFO, or a symlink to a device node, exists but is not something a
    bare `read_bytes()` may safely be pointed at: a FIFO with no writer
    blocks forever and a character device reads without bound, and either
    leaves the run hanging with no output and no exit status at all, which
    Constitution II forbids (T136). `path.exists()` is true for both, which
    is what tells them apart from a broken symlink: that one fails
    `exists()` too, so it falls through to the `read_bytes()` below and is
    reported through the `OSError` it raises instead, preserving T067's
    behavior of reading rather than passing it over.
    """
    return ValidationProblem(
        file=basename,
        found="not a regular file",
        expected="a regular file",
    )


def _collect_entry(
    path: Path,
    relative: str,
    candidates: dict,
    ignored: set,
    problems: list[ValidationProblem],
) -> None:
    basename = path.name
    if not basename.endswith(".toml"):
        # Keyed by the path within the override, not the basename: FR-035
        # requires any file FR-032a marks ignored to be named, and two
        # author-written `notes.md` in different directories reported under
        # one name leave one of them named nowhere.
        ignored.add(relative)
        return
    if path.exists() and not path.is_file():
        problems.append(_not_a_regular_file(basename))
        return
    try:
        data = path.read_bytes()
    except OSError as exc:
        problems.append(_unreadable(basename, exc))
        return
    candidates[basename].append((relative, data))


def _walk_override(root: Path, problems: list[ValidationProblem]):
    """Yield every non-directory entry under `root`, at any depth, with its
    path relative to `root`.

    Walked with `iterdir` rather than `Path.rglob`, which defaults to
    `recurse_symlinks=False` and swallows `OSError`: a subtree behind a
    symlinked directory composed nothing, and an unlistable directory was
    passed over in silence, both while the run reported `packaged` and exited
    0 (FR-028, FR-029).

    A dot-prefixed file or directory is passed over here, and only here.
    FR-032b's line is drawn at authorship: `.git/config` was written by no
    author, and applying the carve-out to a file's own name alone put eighteen
    `ignored` lines from a `.git/` checkout into the report of anyone sharing a
    rule set the obvious way, while letting `.hidden/navy.toml` compose
    silently as a replacement.

    The carve-out is deliberately *not* in `_collect_entry`, which the
    single-file override path also reaches: a location the author typed on the
    command line is not a file a tool left behind, and passing it over made
    `cetools validate override/.navy.toml` print `Rules data is valid.` and
    exit 0 having composed nothing — verbatim the mistyped-path-that-appears-
    to-succeed failure FR-028 exists to remove, and the same reasoning that
    made a `/dev/null` location a usage error rather than a silent no-op.

    Symlinked directories are followed, which is the point, so directories
    already visited are skipped by identity: without that a link pointing at
    its own ancestor walks until the kernel runs out of path, and a link beside
    the directory it points at lists every file beneath it twice. The identity
    check therefore comes before the listing rather than after it, so a
    revisited directory costs nothing and yields nothing.
    """
    stack = [root]
    seen: set[tuple[int, int]] = set()
    while stack:
        directory = stack.pop()
        try:
            identity = directory.stat()
            if (key := (identity.st_dev, identity.st_ino)) in seen:
                continue
            seen.add(key)
            entries = sorted(directory.iterdir())
        except OSError as exc:
            name = str(root) if directory == root else directory.relative_to(root).as_posix()
            problems.append(_unlistable(name, exc))
            continue
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                stack.append(entry)
            else:
                # Not `is_file()`: a broken symlink is neither a file nor a
                # directory, and passing it over would leave a misnamed house
                # rule silently out of force. Reading it reports it instead.
                yield entry, entry.relative_to(root).as_posix()


def _compose(
    override: Path | str | None,
    packaged: dict[str, bytes],
) -> tuple[dict[str, bytes], Provenance, tuple[ValidationProblem, ...]]:
    if override is None:
        provenance = Provenance(version=package_version(), files=(), ignored=())
        return dict(packaged), provenance, ()
    if override == "":
        # `Path("")` is `Path(".")`, which exists and is a directory, so an
        # empty string silently composed the whole current working
        # directory — the ordinary shell mistake of `--rules-data "$DIR"`
        # with `DIR` unset, and no location any author named (FR-028, T137).
        raise RulesDataError("override location is empty")

    override_path = Path(override)
    if not override_path.exists():
        raise RulesDataError(f"override location does not exist: {override_path}")
    # A location that exists but can hold no rules data, a device node or a
    # named pipe, is the same silent failure a mistyped path is: composing it
    # as packaged would put none of the author's house rules in force while
    # appearing to succeed (FR-028).
    if not override_path.is_file() and not override_path.is_dir():
        raise RulesDataError(
            f"override location is neither a file nor a directory: {override_path}"
        )

    problems: list[ValidationProblem] = []
    candidates: dict[str, list[tuple[str, bytes]]] = defaultdict(list)
    ignored: set[str] = set()

    if override_path.is_file():
        _collect_entry(override_path, override_path.name, candidates, ignored, problems)
    else:
        for entry, relative in _walk_override(override_path, problems):
            _collect_entry(entry, relative, candidates, ignored, problems)

    accepted: dict[str, bytes] = {}
    for basename, items in sorted(candidates.items()):
        if len(items) > 1:
            paths = ", ".join(sorted(p for p, _ in items))
            problems.append(
                ValidationProblem(
                    file=basename,
                    found=f"two override files share this basename: {paths}",
                    expected="a single file at this basename",
                )
            )
            continue
        accepted[basename] = items[0][1]

    composed = dict(packaged)
    # `accepted` was filled from `sorted(candidates.items())` above, so this
    # list is already in `file` order and data-model.md's "sorted by file"
    # guarantee holds on that sort. A second `file_provenance.sort()` here was
    # dead, and worse than dead: it read as the line providing the guarantee,
    # so removing the sort that actually provides it would have looked safe.
    file_provenance: list[FileProvenance] = []
    for basename, data in accepted.items():
        disposition = Disposition.REPLACED if basename in packaged else Disposition.ADDED
        composed[basename] = data
        file_provenance.append(
            FileProvenance(file=basename, disposition=disposition, fingerprint=fingerprint(data))
        )

    provenance = Provenance(
        version=package_version(),
        files=tuple(file_provenance),
        ignored=tuple(sorted(ignored)),
    )
    return composed, provenance, tuple(problems)


# --- the validation driver ---------------------------------------------------


def _singleton_slots(basename: str, declared: object) -> set[str]:
    """Which single-instance kinds a file stands for, by what it declared and
    by the basename it carries (FR-029).

    A file rejected before its contents were interpreted still occupies its
    slot, so the absent-kind check must not go on to report it missing: a
    report that names a file and then says there is no such file states
    something false, and rule 2 of contracts/data-files.md asks for no
    further problem from a file rejected on its header (FR-002).

    A third source — the kind declared by the *packaged* file this basename
    replaces — was carried here and was redundant with the second by
    construction: `_CANONICAL_FILE` maps each single-instance kind to the
    packaged basename that declares it, so the two answer identically for
    every shipped file, and `test_canonical_file_names_the_packaged_declarer`
    pins that. Two sources that always agree cannot each be shown to matter,
    which is how all three came to be removable one at a time with the suite
    green.
    """
    slots = set()
    if isinstance(declared, str) and declared in _SINGLETON_KINDS:
        slots.add(declared)
    if (canonical := _KIND_AT_CANONICAL_FILE.get(basename)) is not None:
        slots.add(canonical)
    return slots


def _validate(override: Path | str | None) -> tuple[RulesData | None, ValidationReport]:
    packaged, read_problems = _discover_packaged()
    composed, provenance, compose_problems = _compose(override, packaged)
    problems = [*read_problems, *compose_problems]
    packaged_kind = _packaged_kind_map(packaged)

    # Every file rejected before its contents were interpreted, by the
    # single-instance kinds it stands for, so the presence check below can
    # tell a kind no file declares from one whose file was rejected (FR-002).
    rejected_slots: set[str] = set()
    for read_problem in read_problems:
        rejected_slots |= _singleton_slots(read_problem.file, None)

    parsed: dict[str, tuple[str, dict]] = {}
    for basename in sorted(composed):
        data = composed[basename]
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            problems.append(
                ValidationProblem(
                    file=basename,
                    found=f"could not decode as UTF-8: {exc}",
                    expected="a UTF-8 encoded file",
                )
            )
            rejected_slots |= _singleton_slots(basename, None)
            continue
        try:
            toml_data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            problems.append(
                ValidationProblem(
                    file=basename,
                    found=f"invalid TOML: {exc}",
                    expected="a well-formed TOML document",
                )
            )
            rejected_slots |= _singleton_slots(basename, None)
            continue

        kind = toml_data.get("schema")
        if not isinstance(kind, str) or kind not in _SUPPORTED_VERSION:
            problems.append(
                ValidationProblem(
                    file=basename,
                    found=(
                        "missing" if "schema" not in toml_data else f"unrecognized kind {kind!r}"
                    ),
                    expected=f"one of: {', '.join(sorted(_SUPPORTED_VERSION))}",
                )
            )
            rejected_slots |= _singleton_slots(basename, kind)
            continue

        declared_version = toml_data.get("schema-version")
        supported = _SUPPORTED_VERSION[kind]
        # Typed before it is compared, because `True == 1` and `1.0 == 1`: a
        # file declaring `schema-version = true` passed the version gate and
        # validated clean, while `schema-version = "1"` was refused as a
        # mismatch rather than as the wrong type. Every other integer-valued
        # field in this module carries the same guard (FR-002, FR-020b).
        if "schema-version" in toml_data and (
            not isinstance(declared_version, int) or isinstance(declared_version, bool)
        ):
            problems.append(
                ValidationProblem(
                    file=basename,
                    location="schema-version",
                    found=type_name(declared_version),
                    expected="an integer",
                )
            )
            rejected_slots |= _singleton_slots(basename, kind)
            continue
        if declared_version != supported:
            problems.append(
                ValidationProblem(
                    file=basename,
                    found=(
                        "missing"
                        if "schema-version" not in toml_data
                        else f"version {declared_version!r}"
                    ),
                    expected=f"version {supported}",
                )
            )
            rejected_slots |= _singleton_slots(basename, kind)
            continue

        original_kind = packaged_kind.get(basename)
        if original_kind is not None and original_kind != kind:
            problems.append(
                ValidationProblem(
                    file=basename,
                    found=f"declared kind {kind!r}",
                    expected=(
                        f"kind {original_kind!r}, the kind of the packaged file at this position"
                    ),
                )
            )
            rejected_slots |= _singleton_slots(basename, kind)
            continue

        parsed[basename] = (kind, toml_data)

    resolved_singleton: dict[str, str] = {}
    for kind in _SINGLETON_KINDS:
        declarers = sorted(name for name, (k, _) in parsed.items() if k == kind)
        if not declarers:
            if kind not in rejected_slots:
                problems.append(
                    ValidationProblem(
                        file=_CANONICAL_FILE[kind],
                        found="no file",
                        expected=f"exactly one file declaring kind {kind!r}",
                    )
                )
        elif len(declarers) > 1:
            # `file` stays one composition key and the declarers are named in
            # `found`, which is the shape FR-029a's duplicate-basename problem
            # already uses. Joining the names into `file` gave a consumer
            # grouping by composition key a phantom key matching no file, and
            # one filtering for a name missed the problem entirely, against
            # what contracts/json-output.md and data-model.md type that field
            # as (FR-010a, FR-022).
            problems.append(
                ValidationProblem(
                    file=declarers[0],
                    found=(
                        f"kind {kind!r} declared by {len(declarers)} files: "
                        f"{', '.join(declarers)}"
                    ),
                    expected=f"exactly one file declaring kind {kind!r}",
                )
            )
        else:
            resolved_singleton[kind] = declarers[0]

    task_parameters: TaskParameters | None = None
    if "task-parameters" in resolved_singleton:
        basename = resolved_singleton["task-parameters"]
        task_parameters, sub_problems = parse_task_parameters(parsed[basename][1], basename)
        problems.extend(sub_problems)

    characteristics: CharacteristicRegistry | None = None
    if "characteristics" in resolved_singleton:
        basename = resolved_singleton["characteristics"]
        characteristics, sub_problems = parse_characteristics(parsed[basename][1], basename)
        problems.extend(sub_problems)

    skills: SkillRegistry | None = None
    if "skills" in resolved_singleton:
        basename = resolved_singleton["skills"]
        skills, sub_problems = parse_skills(parsed[basename][1], basename)
        problems.extend(sub_problems)

    benefits: BenefitRegistry | None = None
    if "benefits" in resolved_singleton:
        basename = resolved_singleton["benefits"]
        benefits, sub_problems = parse_benefits(parsed[basename][1], basename)
        problems.extend(sub_problems)

    # Career validation proceeds even when a registry is missing or invalid,
    # against an empty substitute, so every reference cascades into its own
    # problem rather than being silently skipped (research R13).
    career_characteristics = characteristics or CharacteristicRegistry(names=MappingProxyType({}))
    career_skills = skills or SkillRegistry(skills=MappingProxyType({}))
    career_benefits = benefits or BenefitRegistry(items=())

    careers: dict[str, CareerDefinition] = {}
    career_names_seen: dict[str, str] = {}
    for basename, (kind, toml_data) in sorted(parsed.items()):
        if kind != "career":
            continue
        career, sub_problems = _parse_career(
            toml_data, basename, career_characteristics, career_skills, career_benefits
        )
        problems.extend(sub_problems)
        if career is None:
            continue
        if career.name in career_names_seen:
            # One composition key in `file`, both files named in `found`; see
            # the single-instance-kind problem above for why (FR-019b, FR-022).
            both = sorted((basename, career_names_seen[career.name]))
            problems.append(
                ValidationProblem(
                    file=both[0],
                    found=f"both declare the name {career.name!r}: {', '.join(both)}",
                    expected="a name distinct across careers in force",
                )
            )
            continue
        career_names_seen[career.name] = basename
        careers[basename.removesuffix(".toml")] = career

    problems.sort()
    report = ValidationReport(
        provenance=provenance, file_count=len(composed), problems=tuple(problems)
    )

    if (
        problems
        or task_parameters is None
        or characteristics is None
        or skills is None
        or benefits is None
    ):
        return None, report

    return (
        RulesData(
            task_parameters=task_parameters,
            characteristics=characteristics,
            skills=skills,
            benefits=benefits,
            careers=MappingProxyType(careers),
            provenance=provenance,
        ),
        report,
    )


def validate_rules(override: Path | str | None = None) -> ValidationReport:
    """The same composition and validation `load_rules` performs, returning
    the report instead of raising (FR-023).
    """
    _, report = _validate(override)
    return report


@cache
def _load_packaged() -> RulesData:
    rules_data, report = _validate(None)
    if rules_data is None:
        raise RulesDataError("packaged rules data is invalid", problems=report.problems)
    return rules_data


def load_rules(override: Path | str | None = None) -> RulesData:
    """Compose the packaged data set with `override` if given, validate all
    of it, and return the loaded set. Raises `RulesDataError` carrying
    `.problems` if anything is wrong. The no-override call is cached; an
    override call is not, since a caller may edit a file and reload in the
    same process.
    """
    if override is None:
        return _load_packaged()
    rules_data, report = _validate(override)
    if rules_data is None:
        raise RulesDataError("rules data is invalid", problems=report.problems)
    return rules_data


load_rules.cache_clear = _load_packaged.cache_clear
