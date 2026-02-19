# Split github-implement-issue into start/end-implementation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the monolithic `github:implement-issue` skill into `github-projects:start-implementation` and `github-projects:end-implementation`, rename all skill prefixes to `github-projects:`, and add three new script subcommands.

**Architecture:** Two independent SKILL.md files sharing state through conversation context when chained, or re-discovering state when called standalone. One shared bash script with new subcommands for preflight, assignment, and draft PR creation.

**Tech Stack:** Bash (github-projects.sh), YAML frontmatter, Markdown (SKILL.md)

**Design doc:** `docs/plans/2026-02-19-split-github-issue-skills-design.md`

---

### Task 1: Restructure script init and add preflight subcommand

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh`

**Context:** Currently `init` (which calls `detect_repo`, `detect_project`, `detect_status_field`) runs unconditionally at line 253 before dispatch. This means: (a) `preflight` can't run before `init`, and (b) if no project exists, the script dies before reaching any subcommand. We need to restructure so `preflight` runs independently and issue-only subcommands don't require project detection.

**Step 1: Restructure init to not run unconditionally**

Remove the bare `init` call at line 253. Instead:
- `preflight` runs its own checks (no init)
- `issue-view`, `issue-create`, `issue-edit`, `issue-close`, `issue-assign` call only `detect_repo`
- All project subcommands (`get-project-item`, `get-project-fields`, `get-start-date`, `add-to-project`, `set-status`, `set-date`, `count-open-sub-issues`, `table-set-status`) call `init`
- `get-parent` calls only `detect_repo` (GraphQL query, no project needed)

Update the dispatch block:

```bash
case "${1:-}" in
  preflight)            shift; cmd_preflight "$@" ;;
  issue-view)           detect_repo; shift; cmd_issue_view "$@" ;;
  issue-create)         detect_repo; shift; cmd_issue_create "$@" ;;
  issue-edit)           detect_repo; shift; cmd_issue_edit "$@" ;;
  issue-close)          detect_repo; shift; cmd_issue_close "$@" ;;
  issue-assign)         detect_repo; shift; cmd_issue_assign "$@" ;;
  get-project-item)     init; shift; cmd_get_project_item "$@" ;;
  get-project-fields)   init; shift; cmd_get_project_fields "$@" ;;
  get-start-date)       init; shift; cmd_get_start_date "$@" ;;
  add-to-project)       init; shift; cmd_add_to_project "$@" ;;
  set-status)           init; shift; cmd_set_status "$@" ;;
  set-date)             init; shift; cmd_set_date "$@" ;;
  get-parent)           detect_repo; shift; cmd_get_parent "$@" ;;
  count-open-sub-issues) detect_repo; shift; cmd_count_open_sub_issues "$@" ;;
  table-set-status)     init; shift; cmd_table_set_status "$@" ;;
  pr-create-draft)      detect_repo; shift; cmd_pr_create_draft "$@" ;;
  *)
    echo "Usage: $0 <subcommand> [args...]" >&2
    echo "Run '$0 <subcommand> --help' for subcommand help" >&2
    exit 1
    ;;
esac
```

**Step 2: Add `cmd_preflight` function**

Add after the `graphql()` helper, before the issue operations section:

```bash
# --- Preflight ---

cmd_preflight() {
  # Check gh CLI exists
  if ! command -v gh &>/dev/null; then
    echo "FAIL: gh CLI not found. Install from https://cli.github.com/" >&2
    exit 1
  fi

  # Check gh auth
  if ! gh auth status &>/dev/null; then
    echo "FAIL: gh not authenticated. Run 'gh auth login'" >&2
    exit 1
  fi

  # Check scopes
  local scopes
  scopes=$(gh auth status 2>&1)
  if ! echo "$scopes" | grep -q "repo"; then
    echo "FAIL: 'repo' scope not granted. Run 'gh auth refresh -s repo'" >&2
    exit 1
  fi
  if ! echo "$scopes" | grep -q "project"; then
    echo "FAIL: 'project' scope not granted. Run 'gh auth refresh -s project'" >&2
    exit 1
  fi

  echo "OK: gh CLI authenticated with repo + project scopes"
}
```

**Step 3: Update header comment**

Add the three new subcommands to the usage comment at the top of the file:

```
#   preflight                          Verify gh CLI, auth, and scopes
#   issue-assign <number>              Assign issue to current user
#   pr-create-draft <number>           Create draft PR linked to issue
```

**Step 4: Verify syntax**

Run: `bash -n plugins/github-project-tools/scripts/github-projects.sh`
Expected: no output (clean parse)

**Step 5: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat(github-project-tools): add preflight subcommand and restructure init"
```

---

### Task 2: Add issue-assign and pr-create-draft subcommands

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh`

**Step 1: Add `cmd_issue_assign` function**

Add after `cmd_issue_close`:

```bash
cmd_issue_assign() {
  gh issue edit "$1" --repo "$REPO" --add-assignee @me
}
```

**Step 2: Add `cmd_pr_create_draft` function**

Add after `cmd_issue_assign`:

```bash
cmd_pr_create_draft() {
  local number="$1"
  local title
  title=$(gh issue view "$number" --repo "$REPO" --json title --jq '.title')
  gh pr create --repo "$REPO" --draft \
    --title "$title" \
    --body "Closes #${number}"
}
```

**Step 3: Verify syntax**

Run: `bash -n plugins/github-project-tools/scripts/github-projects.sh`
Expected: no output (clean parse)

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat(github-project-tools): add issue-assign and pr-create-draft subcommands"
```

---

### Task 3: Rename github-add-issue skill

**Files:**
- Rename directory: `plugins/github-project-tools/skills/github-add-issue/` → `plugins/github-project-tools/skills/github-projects-add-issue/`
- Modify: the SKILL.md inside (frontmatter name change)

**Step 1: Rename directory**

```bash
git mv plugins/github-project-tools/skills/github-add-issue plugins/github-project-tools/skills/github-projects-add-issue
```

**Step 2: Update frontmatter name**

In `plugins/github-project-tools/skills/github-projects-add-issue/SKILL.md`, change:
- `name: github:add-issue` → `name: github-projects:add-issue`

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/github-projects-add-issue/
git commit -m "feat(github-project-tools): rename github:add-issue to github-projects:add-issue"
```

---

### Task 4: Create github-projects:start-implementation skill

**Files:**
- Create: `plugins/github-project-tools/skills/github-projects-start-implementation/SKILL.md`

**Step 1: Write the SKILL.md**

Create the file with the full skill definition per the design doc. Key sections:

- Frontmatter: `name: github-projects:start-implementation`, description
- Phase 0: Preflight — find script, run `scripts/github-projects.sh preflight`
- Phase 1: Setup — `get-project-fields`, map statuses, note if no project
- Phase 2: Fetch Issue — parse number/URL, `issue-view`, verify open, `get-parent`
- Phase 3: Set Start State — `issue-assign`, project ops (conditional), parent start date (ask user), draft PR (ask user)
- Phase 4: Implement — present issue context
- Phase 5: Handoff — ask user, invoke end-implementation or present can't-implement options

Include all exact bash commands with `scripts/github-projects.sh` prefix. Include the Important Notes section (no variable wrapping, no direct gh calls, extract JSON in-context).

**Step 2: Verify frontmatter**

Check that the YAML frontmatter parses correctly (name and description fields present).

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/github-projects-start-implementation/
git commit -m "feat(github-project-tools): add github-projects:start-implementation skill"
```

---

### Task 5: Create github-projects:end-implementation skill

**Files:**
- Create: `plugins/github-project-tools/skills/github-projects-end-implementation/SKILL.md`

**Step 1: Write the SKILL.md**

Create the file with the full skill definition per the design doc. Key sections:

- Frontmatter: `name: github-projects:end-implementation`, description
- Phase 0: Preflight — find script, run `scripts/github-projects.sh preflight`
- Phase 1: Setup (conditional) — skip if state in context, otherwise auto-detect
- Phase 2: Fetch Issue (conditional) — skip if state in context, otherwise parse and fetch
- Phase 3: Set End State — project ops (conditional), close issue, parent auto-close (ask user)

Include all exact bash commands. Include Important Notes section.

**Step 2: Verify frontmatter**

Check YAML frontmatter parses correctly.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/github-projects-end-implementation/
git commit -m "feat(github-project-tools): add github-projects:end-implementation skill"
```

---

### Task 6: Delete github-implement-issue and update versions

**Files:**
- Delete: `plugins/github-project-tools/skills/github-implement-issue/` (entire directory)
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json` — bump version to `0.3.0`
- Modify: `.claude-plugin/marketplace.json` — bump plugin version to `0.3.0`, bump `metadata.version`

**Step 1: Delete old skill**

```bash
git rm -r plugins/github-project-tools/skills/github-implement-issue
```

**Step 2: Bump plugin.json version**

In `plugins/github-project-tools/.claude-plugin/plugin.json`, change `"version": "0.2.0"` → `"version": "0.3.0"`.

**Step 3: Bump marketplace.json**

In `.claude-plugin/marketplace.json`:
- Update the github-project-tools entry `"version": "0.2.0"` → `"version": "0.3.0"`
- Update `metadata.version` to `"0.3.0"`

**Step 4: Commit**

```bash
git add -A
git commit -m "Release github-project-tools v0.3.0: split implement-issue into start/end-implementation"
```

**Step 5: Tag**

```bash
git tag github-project-tools/v0.3.0
```
