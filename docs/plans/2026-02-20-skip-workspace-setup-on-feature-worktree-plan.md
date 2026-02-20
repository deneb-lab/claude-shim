# Skip Workspace Setup on Feature Worktree — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `start-implementation` skip the workspace setup prompt when already on a secondary git worktree with a feature branch.

**Architecture:** Add a conditional check at the beginning of Phase 3, step 6 in the SKILL.md file. Two git commands detect worktree + feature branch; if both match, skip the rest of the step.

**Tech Stack:** Markdown (SKILL.md prompt file), git CLI commands

---

### Task 1: Add worktree detection conditional to Phase 3, step 6

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:130-148`

**Step 1: Edit the SKILL.md file**

Replace the current step 6 content (lines 130-148) with a version that has a conditional check at the top. The new step 6 should read:

```markdown
6. **Set up the workspace.**

   First, check if the user is already on a non-main worktree:
   ```bash
   git rev-parse --absolute-git-dir
   ```
   If the output contains `.git/worktrees/`, this is a secondary worktree. Then check the current branch:
   ```bash
   git rev-parse --abbrev-ref HEAD
   ```
   If the branch is not `main` (or whatever the default branch is), **skip the rest of this step** and tell the user: "Already on worktree branch `<branch>` — skipping workspace setup."

   Otherwise, ask the user how they want to set up their workspace. Suggest a branch name based on the issue: `feat/<issue-number>-<slug>` where the slug is the issue title lowercased, spaces replaced by hyphens, special characters removed.

   Offer three options:

   a. **Feature branch** (recommended) — create and switch to the branch:
      ```bash
      git checkout -b <branch-name>
      ```

   b. **Git worktree** — ask which directory:
      - `../<repoName>__worktrees/<branch-name>` (recommended — sibling directory, use `basename` of `git rev-parse --show-toplevel` for repoName)
      - `.worktrees/<branch-name>` (project-local, hidden)

      Then create the worktree:
      ```bash
      git worktree add <path> -b <branch-name>
      ```

   c. **Stay on current branch** — skip workspace setup entirely.
```

**Step 2: Verify the edit**

Read the modified file and confirm:
- The conditional check appears before the workspace setup prompt
- The existing three options (branch, worktree, stay) are preserved unchanged
- The `git rev-parse --absolute-git-dir` and `git rev-parse --abbrev-ref HEAD` commands are both present
- The skip message includes the branch name

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): skip workspace setup when on feature worktree"
```

### Task 2: Bump plugin version

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json` — bump version
- Modify: `.claude-plugin/marketplace.json` — mirror the new version

**Step 1: Check current version**

Read `plugins/github-project-tools/.claude-plugin/plugin.json` to find the current version.

**Step 2: Bump patch version**

Increment the patch version (e.g., `0.5.0` → `0.5.1`).

**Step 3: Update marketplace.json**

Update the matching version entry in `.claude-plugin/marketplace.json`.

**Step 4: Commit the version bump**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v<new-version>: skip workspace setup on feature worktree"
```

**Step 5: Tag the release**

```bash
git tag github-project-tools/v<new-version>
```
