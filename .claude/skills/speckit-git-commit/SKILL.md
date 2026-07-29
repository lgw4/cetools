---
name: speckit-git-commit
description: Auto-commit changes after a Spec Kit command completes
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: git:commands/speckit.git.commit.md
---

# Auto-Commit Changes

Automatically stage and commit all changes after a Spec Kit command completes.

## Behavior

This command is invoked as a hook after (or before) core commands. It:

1. Determines the event name from the hook context (e.g., if invoked as an `after_specify` hook, the event is `after_specify`; if `before_plan`, the event is `before_plan`)
2. Checks `.specify/extensions/git/git-config.yml` for the `auto_commit` section
3. Looks up the specific event key to see if auto-commit is enabled
4. Falls back to `auto_commit.default` if no event-specific key exists
5. Determines the commit message based on `commit_style` (see below)
6. If enabled and there are uncommitted changes, runs `git add .` + `git commit`

## Commit Message Styles

Controlled by the `commit_style` key in `.specify/extensions/git/git-config.yml`:

- **`fixed`** (default): use the per-command `message` if configured, otherwise a generic `[Spec Kit] Auto-commit <phase> <command>` message.
- **`conventional`**: inspect the actual changes (`git diff` / `git status`) since the last commit and generate a single-line [Conventional Commit](https://www.conventionalcommits.org/) message (`type(scope): subject`, e.g. `feat: add OAuth specification` or `docs: update implementation plan`) that accurately summarizes the change. Write this message to a temporary file and pass the file's path to the script (see Execution below). The configured `message` values are ignored in this mode.

## Execution

**This project delegates all git operations to the `git-ops` agent.** Do not run
`auto-commit.sh` yourself and do not run `git commit` in the main loop.

Determine the event name from the hook that triggered this command (e.g.
`after_specify`, `before_plan`, `after_implement`), then invoke the Agent tool
with `subagent_type: git-ops`, instructing it to:

1. Read `.specify/extensions/git/git-config.yml` and check the gate for this
   event: `auto_commit.<event_name>.enabled`, falling back to
   `auto_commit.default` when the event key is absent. If the gate is false,
   stop and report that auto-commit is disabled for the event — commit nothing.
2. Run `git status` and `git diff` to see what actually changed.
3. Stage only the paths this Spec Kit phase produced (typically `specs/`, plus
   `src/` and `tests/` for `after_implement`). Do not run `git add .` — the
   working tree may hold unrelated untracked files.
4. Commit with a single-line Conventional Commit message it writes itself from
   the diff (`commit_style: conventional`), e.g. `docs: add widget spec` or
   `feat: implement widget parser`. The static `message:` values in
   `git-config.yml` are ignored in this mode.
5. Not push. Pushing stays an explicit, separate request.

Report back what the agent committed, or that it skipped.

The `auto-commit.sh` / `auto-commit.ps1` scripts remain available for manual or
non-Claude use; the gate check and message generation they perform are covered
by the agent brief above instead.

## Configuration

In `.specify/extensions/git/git-config.yml`:

```yaml
# "fixed" (default) uses the messages below; "conventional" asks the agent
# to generate a Conventional Commit message from the diff instead.
commit_style: fixed

auto_commit:
  default: false          # Global toggle — set true to enable for all commands
  after_specify:
    enabled: true          # Override per-command
    message: "[Spec Kit] Add specification"
  after_plan:
    enabled: false
    message: "[Spec Kit] Add implementation plan"
```

## Graceful Degradation

- If Git is not available or the current directory is not a repository: skips with a warning
- If no config file exists: skips (disabled by default)
- If no changes to commit: skips with a message
- If `commit_style: conventional` is set and no generated message was supplied: fails with a clear error instead of silently falling back to the fixed message format