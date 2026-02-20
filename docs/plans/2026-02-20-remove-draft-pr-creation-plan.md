# Remove Draft PR Creation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the draft PR creation step from start-implementation and the `pr-create-draft` subcommand from the script.

**Architecture:** Pure deletion across SKILL.md and github-projects.sh, plus version bumps in plugin.json and marketplace.json.

**Tech Stack:** Bash script, Markdown skill files, JSON config

---

### Task 1: Remove draft PR step from SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:3` (description frontmatter)
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:9` (intro sentence)
- Modify: `plugins/github-project-tools/skills/start-implementation/SKILL.md:97-104` (Phase 3 step 5 + renumber step 6)

**Step 1: Edit the description frontmatter (line 3)**

Change:
```
description: Start implementing a GitHub issue - assigns, sets dates/status, creates draft PR, and presents issue context
```
To:
```
description: Start implementing a GitHub issue - assigns, sets dates/status, and presents issue context
```

**Step 2: Edit the intro sentence (line 9)**

Change:
```
Start working on a GitHub issue: assign yourself, update project board dates and status, optionally create a draft PR, then present the issue context so you can begin implementation.
```
To:
```
Start working on a GitHub issue: assign yourself, update project board dates and status, then present the issue context so you can begin implementation.
```

**Step 3: Delete Phase 3 step 5 (lines 97-102)**

Remove these lines entirely:
```markdown
5. Ask the user: "Create a draft PR linked to this issue?"
   - If yes:
     ```bash
     scripts/github-projects.sh pr-create-draft <number>
     ```
   - If no, skip this step.
```

**Step 4: Renumber step 6 to step 5 (line 104)**

Change `6. **Set up the workspace.**` to `5. **Set up the workspace.**`

**Step 5: Commit**

```bash
git add plugins/github-project-tools/skills/start-implementation/SKILL.md
git commit -m "feat(github-project-tools): remove draft PR creation from start-implementation"
```

---

### Task 2: Remove pr-create-draft from github-projects.sh

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:17` (usage comment)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:179-187` (function)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:341` (dispatch case)

**Step 1: Remove the usage comment (line 17)**

Delete this line:
```
#   pr-create-draft <number>              Create draft PR linked to issue
```

**Step 2: Delete the cmd_pr_create_draft function (lines 179-187)**

Remove the entire function:
```bash
cmd_pr_create_draft() {
  [[ -n "${1:-}" ]] || { echo "pr-create-draft: <number> required" >&2; exit 1; }
  local number="$1"
  local title
  title=$(gh issue view "$number" --repo "$REPO" --json title --jq '.title')
  gh pr create --repo "$REPO" --draft \
    --title "$title" \
    --body "Closes #${number}"
}
```

**Step 3: Remove the dispatch case (line 341)**

Delete this line:
```
  pr-create-draft)      detect_repo; shift; cmd_pr_create_draft "$@" ;;
```

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat(github-project-tools): remove pr-create-draft subcommand from script"
```

---

### Task 3: Bump versions

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json:4` (version)
- Modify: `.claude-plugin/marketplace.json:8,15` (metadata version + plugin version)

**Step 1: Bump plugin.json version**

Change `"version": "0.7.0"` to `"version": "0.8.0"` in `plugins/github-project-tools/.claude-plugin/plugin.json`.

**Step 2: Bump marketplace.json versions**

In `.claude-plugin/marketplace.json`:
- Change `"version": "0.7.0"` to `"version": "0.8.0"` in `metadata`
- Change `"version": "0.7.0"` to `"version": "0.8.0"` for the github-project-tools plugin entry

**Step 3: Commit**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v0.8.0: remove draft PR creation from start-implementation"
```
