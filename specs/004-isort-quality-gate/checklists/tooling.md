# Tooling Configuration Requirements Checklist: isort Quality Gate and Pre-Commit Support

**Purpose**: Validate that configuration, workflow, and compatibility requirements are complete, clear, and measurable before implementation
**Created**: 2026-06-18
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)
**Audience**: PR reviewer
**Depth**: Standard — both configuration requirements and developer workflow requirements

---

## Configuration Requirements Completeness

- [x] CHK001 — Are specific version pins (e.g., exact rev tags) documented for each pre-commit hook (isort, Black, flake8) rather than left to implementer discretion? [Completeness, Spec §FR-005]
  - **PASS**: FR-005 explicitly requires pinning to a specific release tag and names `pre-commit autoupdate` as the update mechanism. Clarifications session confirms the strategy. Actual version values are correctly deferred to research.md.
- [x] CHK002 — Are all four quality checks (isort, Black, flake8, pytest) unambiguously mapped to a specific hook runner type (upstream repo vs local) in requirements? [Clarity, Spec §FR-002, FR-003]
  - **PASS (implementation detail)**: Hook runner type (upstream repo vs local) is a how-to decision appropriately deferred to research.md and the implementation. The spec correctly states the "what" (all four checks run as pre-push hooks) without prescribing the YAML mechanism.
- [x] CHK003 — Does the spec define which `stages:` value applies to each hook, or does it only say "pre-push" for hooks as a group? [Completeness, Spec §FR-003]
  - **PASS**: FR-003 and the Assumptions section both state "pre-push" as the stage for all hooks. The YAML `stages:` key name is implementation detail correctly deferred.
- [x] CHK004 — Is the required `[tool.isort]` field set fully enumerated (profile, line_length, src_paths) in requirements, or are some fields left to implementer judgment? [Completeness, Spec §FR-004]
  - **FIXED**: FR-004 previously omitted `line_length = 99` — a genuine gap because isort defaults to 79, which would conflict with Black's 99 setting and cause every line over 79 chars to be flagged. **Spec amended**: FR-004 now explicitly requires `profile = "black"` and `line_length = 99`. `src_paths` is referenced in Key Entities and is an implementation detail; no change needed there.
- [x] CHK005 — Is it unambiguous whether isort should run in check-only mode or auto-fix mode during the pre-push hook? [Clarity, Gap]
  - **FIXED**: No functional requirement previously stated check-only mode. US1 Scenario 1 implied it ("rejected, shown which files") but auto-fix would silently modify staged files — meaningfully different and surprising UX. **Spec amended**: FR-009 added, requiring check-only mode (non-zero exit, no file modifications; developer fixes manually).
- [x] CHK006 — Are the PyPI version floor pins (`>=5.13`, `>=3`) explicitly reconciled with the hook rev pinning strategy (exact tag) in requirements? [Consistency, Spec §FR-005, FR-007, FR-008]
  - **PASS (implementation detail)**: FR-005 governs hook rev tags; FR-007/FR-008 state dev dependency addition without prescribing version pin style. Floor vs exact PyPI pinning is a conventional uv/pip decision appropriately deferred. No inconsistency in requirements.
- [x] CHK007 — Is the required content and exact location of the new AGENTS.md "Hooks" subsection precisely specified (subsection name, parent section, exact command)? [Clarity, Spec §FR-006]
  - **PASS**: FR-006 names the subsection ("Hooks"), the parent section ("Setup"), the exact command (`pre-commit install --hook-type pre-push`), and the context ("so new contributors run it alongside `uv sync`"). Fully specified.
- [x] CHK008 — Is there a requirement specifying which hook configuration fields are mandatory vs optional (e.g., `pass_filenames: false` for pytest)? [Completeness, Gap]
  - **PASS (implementation detail)**: YAML field-level config (e.g., `pass_filenames`, `language`) is an implementation concern appropriately captured in research.md (data-model.md §Validation Rules). The spec correctly operates at the "what" level.

---

## isort-Black Compatibility Requirements

- [x] CHK009 — Is the `profile = "black"` requirement explicitly linked to the Black formatting requirement rather than stated in isolation? [Consistency, Spec §FR-004]
  - **PASS**: FR-004 explicitly states `profile = "black"` and qualifies it with "so its output never conflicts with Black's formatting." The causal link to Black is unambiguous in the requirement text itself.
- [x] CHK010 — Is the requirement to match `line_length` between isort and Black explicitly stated with the target value (99), not just implied? [Clarity, Spec §FR-004]
  - **PASS**: FR-004 explicitly requires "MUST use the same `line_length` as Black (99)" — the target value 99 is stated, not implied.
- [x] CHK011 — Is the requirement that `src_paths` must include `["src", "tests"]` for correct first-party import classification documented, or left to implementer inference? [Clarity, Gap]
  - **PASS (implementation detail)**: Key Entities acknowledges "source paths" under `[tool.isort]`. CHK004's prior resolution explicitly classified `src_paths` values as an implementation detail correctly deferred to research.md. The spec specifies the configuration location (`pyproject.toml` under `[tool.isort]`) without prescribing exact path values, which is the appropriate level for a requirement.
- [x] CHK012 — Is there a requirement specifying what to do when a future Black or isort update changes formatting behavior incompatibly (deliberate `pre-commit autoupdate` only)? [Edge Case, Gap]
  - **PASS**: FR-005's pinning strategy (specific release tags + deliberate `pre-commit autoupdate`) is the policy. Incompatible changes cannot occur silently — because updates are always deliberate, compatibility can be verified before committing to an upgrade. No additional requirement is needed beyond FR-005.

---

## Developer Workflow Requirements

- [x] CHK013 — Is the one-time hook installation command specified precisely, including the exact flag (`--hook-type pre-push`) and without ambiguity about when to run it relative to `uv sync`? [Clarity, Spec §FR-006]
  - **PASS**: FR-006 names the exact command (`pre-commit install --hook-type pre-push`), the exact flag, the AGENTS.md subsection ("Hooks" inside "Setup"), and the timing ("alongside `uv sync`"). No implementer discretion required.
- [x] CHK014 — Are requirements defined for the error output a developer sees when a hook fails — is format or verbosity specified, or assumed to be tool-default? [Clarity, Gap]
  - **PASS (implementation detail)**: US1 Scenario 1 and FR-009 together specify the observable outcome ("shown which file(s) have unsorted imports, exits non-zero") without prescribing format. Tool-default output satisfies the requirement as written; specifying format would over-constrain the implementation.
- [x] CHK015 — Is the requirement that `uv sync` alone installs both `pre-commit` and `isort` (no separate pip steps) stated explicitly? [Clarity, Spec §FR-007, FR-008]
  - **PASS**: FR-007 is explicit ("so it is installed by `uv sync`"); FR-008 adds pre-commit as a dev dep; the Assumptions section states "picked up by that existing command without additional steps." The combined coverage is unambiguous.
- [x] CHK016 — Are requirements defined for running the full quality gate manually (outside of git push), or is manual invocation addressed only in `quickstart.md`? [Completeness, Gap]
  - **FIXED**: Gap confirmed — no requirement scoped manual invocation. **Spec amended**: Assumptions section now explicitly states that manual quality gate invocation (`pre-commit run --all-files`) is out of scope for this feature's requirements and belongs in `quickstart.md`. This prevents implementer confusion about what AGENTS.md must contain.
- [x] CHK017 — Are requirements defined for the developer experience when `pre-commit` is missing from the environment at hook invocation time? [Edge Case, Spec §Edge Cases]
  - **PASS**: FR-007/FR-008 make both tools dev dependencies installed by `uv sync`, so this scenario only arises if setup is skipped. The Edge Cases section acknowledges it ("setup step must surface a clear error or install `pre-commit`"); the dev dependency approach satisfies the "install as part of setup" branch. Sufficient for a single-developer project where `uv sync` is the established entry point.
- [x] CHK018 — Is the "re-sort and re-push" recovery flow (US1 Scenario 3) specified clearly enough that a developer can follow it without reading the quickstart guide? [Clarity, Spec §US1]
  - **FIXED**: US1 Scenario 3 said "runs the import sorter manually" without specifying the command. FR-006 required only the hook-installation command. **Spec amended**: FR-006 now additionally requires AGENTS.md to document the manual sort command (`uv run isort .`) so a developer receiving an isort failure can resolve it without consulting external documentation.

---

## Acceptance Criteria Measurability

- [x] CHK019 — Is "push is blocked 100% of the time" (SC-001) testable in a local environment without CI, or does it require instrumentation not specified in requirements? [Measurability, Spec §SC-001]
  - **PASS**: SC-001's "when hooks are installed" qualifier bounds the claim to a deterministic hook setup. The criterion is locally testable by staging a file with unsorted imports and running `git push` — no CI or additional instrumentation required.
- [x] CHK020 — Is the 2-minute setup time threshold (SC-003) qualified with a machine context (e.g., "after `uv sync` completes") to make it objectively measurable? [Measurability, Spec §SC-003]
  - **PASS**: SC-003 already includes "on a machine where `uv sync` has already completed" — the precise machine-context qualification the item asks about. The threshold is objectively measurable given that pre-condition.
- [x] CHK021 — Is "zero new failing tests" (SC-004) scoped to the full test suite, to a specific test file, or to tests newly introduced by this feature? [Clarity, Spec §SC-004]
  - **PASS**: SC-004 scopes to "the existing test suite" with the causal qualifier "as a result of this change." Both the scope (full existing suite, not just new tests) and causal direction (regressions from this feature only) are unambiguous. Verifiable by running `uv run pytest` before and after.
- [x] CHK022 — Is SC-005 ("isort reports zero violations") expressed as a runnable command with an expected exit code, or only as a prose statement? [Clarity, Spec §SC-005]
  - **FIXED**: SC-005 was prose only ("isort reports zero violations") with no verifiable command or exit code. A developer couldn't confirm it without knowing the command independently. **Spec amended**: SC-005 now reads "Running `uv run isort --check-only .` exits with code 0 on the current codebase after the initial sort is applied" — consistent with FR-009's check-only mode requirement.

---

## Scenario Coverage

- [x] CHK023 — Are requirements defined for what happens when a hook fails mid-suite (e.g., isort fails — does Black still run, or does the suite abort)? [Coverage, Gap]
  - **PASS (implementation detail)**: FR-003 requires all checks to run as pre-push hooks but correctly does not prescribe hook runner sequencing or failure aggregation — those are pre-commit internals. The user stories (US1, US2) each describe individual failure scenarios, which is consistent with pre-commit's standard fail-fast behavior. Specifying sequencing would over-constrain the implementation.
- [x] CHK024 — Is the scenario where `.pre-commit-config.yaml` exists but `pre-commit install` was never run (hooks silently skipped) addressed in requirements? [Edge Case, Gap]
  - **PASS (intentional scope boundary)**: FR-006 requires the install command to be documented in AGENTS.md; US3 requires "when the developer runs the standard setup command, hooks are installed and active." A developer who ignores documentation will lack hook coverage — but this is universally out of scope for any tooling requirement. Auto-installation without explicit developer action would require a mechanism (e.g., post-install script) that this feature deliberately does not introduce.
- [x] CHK025 — Are requirements defined for the scenario where the developer has uncommitted working-tree changes when the pre-push hook fires? [Coverage, Gap]
  - **PASS (pre-push stage semantics)**: For `pre-push` stage hooks, pre-commit passes only files present in the commits being pushed, not working-tree-only changes. This is intrinsic to the `pre-push` stage and not an edge case requiring a separate requirement. FR-003's specification of `pre-push` as the stage implicitly handles this correctly.
- [x] CHK026 — Is the new-contributor onboarding scenario (US3) testable with measurable criteria beyond "hooks are installed and active"? [Measurability, Spec §US3]
  - **PASS**: US3 Scenario 2 ("blocked identically to the experience of an existing contributor") is testable: stage a file with unsorted imports in a fresh-clone environment and attempt a push, expecting a blocked push with an isort error. SC-001 and SC-003 provide the measurability anchors for "active" and "setup time." "Identically" is appropriate user-story language; it does not require exact error-message specification.

---

## Edge Cases & Boundary Conditions

- [x] CHK027 — Is the `--no-verify` bypass behavior explicitly scoped (permitted and not prohibited) in requirements, with no obligation to prevent it? [Clarity, Spec §Edge Cases]
  - **PASS**: Edge Cases explicitly states "this spec does not prohibit `--no-verify`; it only installs the hooks." The bypass is acknowledged as available standard git behavior, out-of-scope for this feature to prevent, and any future CI/CD gate is named as the eventual backstop. Fully scoped.
- [x] CHK028 — Is the behavior when isort and Black produce incompatible output (despite `profile = "black"`) defined as a named failure mode in requirements, even if only to say it must not occur? [Edge Case, Spec §Edge Cases]
  - **PASS**: FR-004 requires the configuration that prevents incompatibility (`profile = "black"` + `line_length = 99`), and Edge Cases acknowledges the scenario with its solution. Defining a separate named failure mode for a scenario the requirements are designed to eliminate would be redundant and potentially misleading. The prevention requirement IS the answer.
- [x] CHK029 — Is there a requirement clarifying whether the initial `isort .` sort (to fix any existing violations) is part of this feature's implementation scope? [Completeness, Spec §SC-005]
  - **PASS**: SC-005's qualifier "after the initial sort is applied" implicitly scopes the initial sort as an implementation task — the success criterion is only achievable if the sort is performed. The plan.md confirms this reading ("the isort initial sort applies the Black profile uniformly"). A separate formal FR would be redundant.
- [x] CHK030 — Is the pinning requirement (FR-005) clarified to address the local pytest hook, which has no upstream repo and therefore no "release tag" to pin? [Clarity, Spec §FR-005]
  - **FIXED**: FR-005 previously said "each hook MUST be pinned to a specific release tag" without exception, making it unresolvable for the `repo: local` pytest hook, which has no upstream release. **Spec amended**: FR-005 now scopes the pinning requirement to "each hook sourced from an upstream repository" and explicitly exempts the local pytest hook, noting its version is implicitly pinned by `pyproject.toml` dev dependencies.

---

## Dependencies & Assumptions

- [x] CHK031 — Is the assumption that `uv run` resolves the correct `.venv` for the local pytest hook explicitly validated as a documented prerequisite, not just a research finding? [Assumption, Gap]
  - **PASS (implementation detail)**: The spec Assumptions correctly document `uv sync` as the environment setup mechanism. The specific invocation strategy for the local pytest hook (`uv run pytest` vs. direct) is an implementation detail appropriately captured in research.md. No spec-level prerequisite beyond "all developers use `uv sync`" is needed.
- [x] CHK032 — Is the platform scope (macOS/Linux with standard git CLI) stated as an explicit assumption in requirements, or only implied? [Assumption, Spec §Assumptions]
  - **FIXED**: The spec Assumptions scoped by git client type ("standard `git` CLI") but did not name the OS, while plan.md explicitly states "macOS/Linux with standard `git` CLI." A Windows developer reading the spec alone would not know whether this feature applies to them. **Spec amended**: Assumptions now explicitly state "The target platform is macOS and Linux developer workstations; Windows is out of scope," consistent with the plan.
- [x] CHK033 — Is the absence of CI/CD enforcement documented as an explicit out-of-scope assumption, so reviewers understand local hooks are the sole guard? [Assumption, Spec §Assumptions]
  - **PASS**: Assumptions explicitly state "No CI/CD pipeline exists yet; this feature focuses solely on local pre-push enforcement." Edge Cases also names CI/CD as the future backstop for `--no-verify` bypasses. The constraint is clearly communicated in two places.

---

## Notes

- Mark items `[x]` when the requirement passes review; add a comment with the location where the requirement is satisfied.
- Items marked `[Gap]` flag requirements that may be absent — confirm whether the gap is intentional or needs a spec amendment.
- All high-risk items resolved: CHK005 (check-only mode), CHK010 (line_length explicit value), CHK018 (recovery command in AGENTS.md), CHK022 (SC-005 runnable command), CHK030 (FR-005 local hook exemption).
