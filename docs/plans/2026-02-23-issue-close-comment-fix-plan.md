# Issue-Close Comment Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** When `issue-close --comment` is called on an already-closed issue, ensure the comment is still posted via `gh issue comment` fallback.

**Architecture:** Add `--comment-file` flag to `cmd_issue_close`, check issue state before closing, and fall back to `gh issue comment` when the issue is already closed.

**Tech Stack:** Bash, `gh` CLI

---

### Task 1: Add `--comment-file` flag and state-checking logic to `cmd_issue_close`

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:15` (usage comment)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:171-183` (`cmd_issue_close`)

**Step 1: Update the usage comment**

Change line 15 from:
```
#   issue-close <number> [--comment C]    Close issue as completed (optional comment)
```
to:
```
#   issue-close <number> [--comment C]    Close issue as completed (optional comment, --comment-file)
```

**Step 2: Rewrite `cmd_issue_close`**

Replace lines 171-183 with:

```bash
cmd_issue_close() {
  local number="$1"; shift
  local comment="" comment_file=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --comment) comment="$2"; shift 2 ;;
      --comment-file) comment_file="$2"; shift 2 ;;
      *) echo "issue-close: unknown arg: $1" >&2; exit 1 ;;
    esac
  done
  # --comment-file overrides --comment
  if [[ -n "$comment_file" ]]; then
    comment=$(cat "$comment_file")
  fi
  # Check current issue state
  local state
  state=$(gh issue view "$number" --repo "$REPO" --json state --jq '.state')
  if [[ "$state" == "OPEN" ]]; then
    local -a cmd=(gh issue close "$number" --repo "$REPO" --reason completed)
    [[ -n "$comment" ]] && cmd+=(--comment "$comment")
    "${cmd[@]}"
  else
    echo "Issue #$number is already closed — skipping close." >&2
    if [[ -n "$comment" ]]; then
      if [[ -n "$comment_file" ]]; then
        gh issue comment "$number" --repo "$REPO" --body-file "$comment_file"
      else
        gh issue comment "$number" --repo "$REPO" --body "$comment"
      fi
    fi
  fi
}
```

Key decisions:
- When the issue is already closed and `--comment-file` was provided, use `gh issue comment --body-file` (avoids multi-line shell escaping issues).
- When `--comment` (inline) was provided, use `gh issue comment --body` (fine for short strings).
- Prints an informational message to stderr when skipping close, so the caller sees what happened.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "fix(github-project-tools): handle already-closed issue in issue-close --comment"
```

---

### Task 2: Update the end-implementation skill to use `--comment-file`

The end-implementation skill currently passes the summary inline as `--comment "$SUMMARY"`. Since summaries are multi-line markdown, switch to `--comment-file` to avoid shell escaping issues.

**Files:**
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md:96-103`

**Step 1: Update Phase 3, step 2**

Replace lines 96-103:
```markdown
2. Close the issue. If `SUMMARY` is non-empty (from Phase 2.5), include it as a closing comment:
   ```bash
   scripts/github-projects.sh issue-close <number> --comment "$SUMMARY"
   ```
   If `SUMMARY` is empty, close without a comment:
   ```bash
   scripts/github-projects.sh issue-close <number>
   ```
```

With:
```markdown
2. Close the issue. If `SUMMARY` is non-empty (from Phase 2.5), write it to a temp file and include it as a closing comment:
   - Write the summary to `/tmp/issue-close-comment.md` using the Write tool
   - Then close:
     ```bash
     scripts/github-projects.sh issue-close <number> --comment-file /tmp/issue-close-comment.md
     ```
   If `SUMMARY` is empty, close without a comment:
   ```bash
   scripts/github-projects.sh issue-close <number>
   ```
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): use --comment-file in end-implementation skill"
```

---

### Task 3: Bump version and update marketplace

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json` (version bump)
- Modify: `.claude-plugin/marketplace.json` (version sync)

**Step 1: Determine new version**

Current version is `0.10.1`. This is a bugfix, so bump to `0.10.2`.

**Step 2: Update plugin.json**

Change `"version": "0.10.1"` to `"version": "0.10.2"` in `plugins/github-project-tools/.claude-plugin/plugin.json`.

**Step 3: Update marketplace.json**

Change the version for `github-project-tools` from `"0.10.1"` to `"0.10.2"` in `.claude-plugin/marketplace.json`. Also bump `metadata.version` if needed.

**Step 4: Commit, tag, push**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v0.10.2: fix issue-close comment on already-closed issues"
git tag github-project-tools/v0.10.2
git push && git push origin github-project-tools/v0.10.2
```
