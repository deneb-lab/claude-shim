# Skip Workspace Setup When Already on Feature Worktree

## Problem

The `start-implementation` skill always asks the user how to set up their workspace (branch, worktree, or stay), even when the user is already on a secondary git worktree on a feature branch. This is unnecessary and disruptive.

## Solution

Add an inline conditional check at the beginning of Phase 3, step 5 in `start-implementation/SKILL.md`.

### Detection Logic

Two git commands determine if workspace setup should be skipped:

1. `git rev-parse --absolute-git-dir` — if the output contains `.git/worktrees/`, this is a secondary worktree (not the main working tree).
2. `git rev-parse --abbrev-ref HEAD` — if the branch is not `main` (or the default branch), the user is on a feature branch.

### Behavior

- **Both conditions true**: Skip step 5. Print "Already on worktree branch `<branch>` — skipping workspace setup."
- **Either condition false**: Proceed with existing step 5 (offer branch/worktree/stay options).

### Scope

- Only step 5 (workspace setup) is affected.
- Draft PR creation (step 4) remains unchanged.
- No changes to `allowed-tools` (already includes `Bash(git:*)`).

### File Changed

`plugins/github-project-tools/skills/start-implementation/SKILL.md` — Phase 3, step 5.
