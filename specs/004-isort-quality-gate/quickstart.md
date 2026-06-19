# Quickstart Validation Guide: isort Quality Gate and Pre-Commit Support

This guide documents how to verify the feature works end-to-end after implementation. It covers
the three acceptance scenarios from the spec.

## Prerequisites

- Repository cloned; `uv sync` completed (installs `isort` and `pre-commit` as dev deps)
- `pre-commit install --hook-type pre-push` run once to install hooks
- A clean working tree on a non-main branch

## Scenario 1: Push blocked by unsorted imports (US1, SC-001)

```bash
# 1. Create a test file with deliberately unsorted imports
cat > /tmp/test_unsorted.py << 'EOF'
import os
import sys
import json
from cetools.engine import dice
EOF
cp /tmp/test_unsorted.py src/cetools/_validate_isort_test.py

# 2. Stage and commit (commit-stage hook does NOT run; only pre-push fires)
git add src/cetools/_validate_isort_test.py
git commit -m "test: deliberate unsorted-import file"

# 3. Attempt push — expect rejection
git push
```

**Expected outcome**: Push is blocked. isort reports which file(s) have unsorted imports and shows
a diff of what it would fix. Exit code is non-zero.

```bash
# Cleanup
git reset HEAD~1
rm src/cetools/_validate_isort_test.py
```

---

## Scenario 2: Push succeeds when all checks pass (US1 SC-002, US2 SC-004)

```bash
# 1. Create a file with correctly sorted imports
cat > /tmp/test_sorted.py << 'EOF'
import json
import os
import sys
EOF
cp /tmp/test_sorted.py src/cetools/_validate_isort_ok.py

# 2. Stage, commit, and push
git add src/cetools/_validate_isort_ok.py
git commit -m "test: correctly sorted import file"
git push
```

**Expected outcome**: All four hooks pass silently. Push completes normally.

```bash
# Cleanup
git rm src/cetools/_validate_isort_ok.py
git commit -m "test: remove validation test file"
git push
```

---

## Scenario 3: Developer fixes unsorted imports and re-pushes (US1 SC-003)

Following Scenario 1:

```bash
# 1. Fix the imports
uv run isort src/cetools/_validate_isort_test.py

# 2. Re-stage the fixed file
git add src/cetools/_validate_isort_test.py

# 3. Amend commit and push
git commit --amend --no-edit
git push --force-with-lease
```

**Expected outcome**: Push succeeds — isort reports zero violations on the fixed file.

---

## Scenario 4: Full quality gate — flake8 violation blocked (US2 SC-001)

```bash
# 1. Introduce a deliberate flake8 violation
cat >> src/cetools/formatter.py << 'EOF'

unused_var = 1  # F841
EOF
git add src/cetools/formatter.py
git commit -m "test: deliberate flake8 violation"
git push
```

**Expected outcome**: Push blocked by flake8 hook. Error reports `F841 local variable 'unused_var' is assigned to but never used`.

```bash
# Cleanup — revert the change
git reset HEAD~1
git checkout -- src/cetools/formatter.py
```

---

## Scenario 5: New contributor onboarding (US3)

```bash
# In a fresh clone:
git clone <repo-url> cetools-fresh
cd cetools-fresh
uv sync                                         # installs isort, pre-commit, all dev deps
uv run pre-commit install --hook-type pre-push  # registers the pre-push hook
git push                                        # triggers hooks on next push
```

**Expected outcome**: Hooks are registered after `pre-commit install`. Subsequent pushes are
identical to an existing contributor's experience.

---

## Verifying SC-005: Zero isort violations on current codebase

```bash
uv run isort --check-only --diff src tests
```

**Expected outcome**: No output, exit code 0 (or a diff that is then fixed by running `uv run isort .`).

---

## Running the full quality gate manually

```bash
uv run isort --check-only --diff src tests
uv run black --check src tests
uv run flake8 src tests
uv run pytest
```

All four commands must exit 0 before the implementation is considered complete.
