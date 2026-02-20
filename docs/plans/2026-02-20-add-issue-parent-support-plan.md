# Add-Issue Parent Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable the `add-issue` skill to link newly created issues to a parent issue via a new `set-parent` script subcommand.

**Architecture:** Add a `set-parent` subcommand to `github-projects.sh` that wraps the `addSubIssue` GraphQL mutation, then add an optional parent-linking phase to the `add-issue` SKILL.md between issue creation and reporting.

**Tech Stack:** Bash, GitHub GraphQL API, Markdown (SKILL.md)

---

### Task 1: Add `set-parent` subcommand to `github-projects.sh`

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:6` (header comment)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:261` (after existing mutations)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:315` (dispatch table)

**Step 1: Add subcommand to header comment**

In the header comment block (lines 2-22), add after line 21 (`count-open-sub-issues`):

```
#   set-parent <child-id> <parent-id>      Set parent issue (add as sub-issue)
```

This goes between `count-open-sub-issues` and `table-set-status`.

**Step 2: Add `cmd_set_parent` function**

After `cmd_set_date()` (which ends around line 297) and before the `# --- Main dispatch ---` comment (line 299), add:

```bash
cmd_set_parent() {
  [[ -n "${1:-}" ]] || { echo "set-parent: <child-node-id> required" >&2; exit 1; }
  [[ -n "${2:-}" ]] || { echo "set-parent: <parent-node-id> required" >&2; exit 1; }
  graphql '
    mutation($parent: ID!, $child: ID!) {
      addSubIssue(input: {issueId: $parent, subIssueId: $child}) {
        subIssue { id }
      }
    }' -f parent="$2" -f child="$1" \
    --jq '.data.addSubIssue.subIssue.id'
}
```

**Step 3: Add dispatch entry**

In the `case` dispatch block, add after the `count-open-sub-issues` line (line 316):

```bash
  set-parent)           detect_repo; shift; cmd_set_parent "$@" ;;
```

Note: `detect_repo` is sufficient — no project fields needed for this mutation.

**Step 4: Verify the script parses correctly**

Run:
```bash
bash -n plugins/github-project-tools/scripts/github-projects.sh
```
Expected: No output (clean parse).

**Step 5: Verify the subcommand is wired up**

Run:
```bash
plugins/github-project-tools/scripts/github-projects.sh set-parent
```
Expected: Error message `set-parent: <child-node-id> required` (exit code 1).

**Step 6: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat(github-project-tools): add set-parent subcommand to github-projects.sh"
```

---

### Task 2: Add parent linking phase to `add-issue` SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/SKILL.md`

**Step 1: Update Phase 1 to gather parent context**

Replace the Phase 1 section (lines 10-19) with:

```markdown
## Phase 1: Gather Context

Read the conversation context and any arguments provided. You need:
- **Title:** A clear, concise issue title
- **Body:** Issue description with enough detail to act on
- **Parent (optional):** If the user mentioned a parent issue (e.g., `parent #31`, `make #31 the parent`, `parent https://github.com/owner/repo/issues/31`), extract the parent reference. Support both `#N` (same repo) and full GitHub URLs (cross-repo).

If the context is insufficient, ask the user for clarification.

The default repository is the current git repository (auto-detected by the script). The user can specify a different repo.
The default project is auto-detected from the repo owner's GitHub projects.
```

**Step 2: Add Phase 2.5 after Phase 2**

After Phase 2's step 4 (line 49, `set-status "$ITEM_ID" todo`), add:

```markdown
## Phase 2.5: Link Parent (conditional)

Skip this phase if no parent was specified in Phase 1.

1. Resolve the parent issue's node ID:
   - Same-repo (`#N`):
     ```bash
     scripts/github-projects.sh issue-view <N> --json id --jq '.id'
     ```
   - Cross-repo (full URL):
     ```bash
     scripts/github-projects.sh issue-view <url> --json id --jq '.id'
     ```

   Save the output as `PARENT_NODE_ID`.

2. Link the new issue as a sub-issue of the parent:
   ```bash
   scripts/github-projects.sh set-parent "$NODE_ID" "$PARENT_NODE_ID"
   ```
```

**Step 3: Update Phase 3 to report parent link**

Replace the Phase 3 section (lines 51-53) with:

```markdown
## Phase 3: Report

Tell the user the issue was created and provide the URL.

If a parent was linked in Phase 2.5, also report: "Linked as sub-issue of #N (title)."
```

**Step 4: Review the complete SKILL.md**

Read the file and verify:
- Phase numbering is consistent (1, 2, 2.5, 3)
- No dangling references or broken formatting
- Important Notes section is unchanged

**Step 5: Commit**

```bash
git add plugins/github-project-tools/skills/add-issue/SKILL.md
git commit -m "feat(github-project-tools): add parent issue support to add-issue skill"
```

---

### Task 3: Bump version and update marketplace

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current versions**

Read both files to determine current version numbers.

**Step 2: Bump plugin version**

In `plugins/github-project-tools/.claude-plugin/plugin.json`, bump the `version` field (minor bump, e.g., `0.5.0` → `0.6.0`).

**Step 3: Update marketplace.json**

In `.claude-plugin/marketplace.json`:
- Update the `github-project-tools` entry's `version` to match
- Bump `metadata.version` if the catalog changed

**Step 4: Commit and tag**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v0.6.0: add-issue parent support"
git tag github-project-tools/v0.6.0
```
