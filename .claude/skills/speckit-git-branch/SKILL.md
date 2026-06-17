---
name: speckit-git-branch
description: Create and switch to a new git feature branch for the current Spec Kit feature
compatibility: Requires spec-kit project structure with .specify/ directory and a git repository
metadata:
  author: local
  source: git-branch:commands/speckit.git.branch.md
---

# Create Git Branch

Create and switch to a new git feature branch before running `/speckit-specify`.

## Behavior

Derives a branch name from the feature description using the same sequential numbering
as the spec directory (scanning `specs/` for the highest existing prefix, then incrementing).
Runs `git checkout -b <branch>` to create the branch, or switches to it if it already exists.

Outputs JSON: `{"BRANCH_NAME": "...", "FEATURE_NUM": "..."}` for the calling skill to consume.

## Execution

**Bash**: `.specify/scripts/bash/create-git-branch.sh --json [--short-name <name>] [--number N] [--timestamp] [feature description]`

Pass the feature description as positional arguments so the script can derive the branch name.
Use `--short-name` to override the auto-generated name.
Use `--dry-run` to compute the branch name without creating it or switching.
