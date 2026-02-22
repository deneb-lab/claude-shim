# End-Implementation Summary Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a closing comment with an auto-generated implementation summary when end-implementation closes an issue.

**Architecture:** Extend `cmd_issue_close` in `github-projects.sh` with an optional `--comment` flag, then add a summary generation phase to the end-implementation SKILL.md that uses it.

**Tech Stack:** Bash (script), Markdown (skill prompt)

---

### Task 1: Add --comment flag to issue-close in github-projects.sh

**Files:**
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:15` (header comment)
- Modify: `plugins/github-project-tools/scripts/github-projects.sh:169-171` (cmd_issue_close function)

**Step 1: Update the header comment**

Change line 15 from:
```
#   issue-close <number>                  Close issue as completed
```
to:
```
#   issue-close <number> [--comment C]    Close issue as completed (optional comment)
```

**Step 2: Replace the cmd_issue_close function**

Replace the existing function (lines 169-171):
```bash
cmd_issue_close() {
  gh issue close "$1" --repo "$REPO" --reason completed
}
```

With:
```bash
cmd_issue_close() {
  local number="$1"; shift
  local comment=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --comment) comment="$2"; shift 2 ;;
      *) echo "issue-close: unknown arg: $1" >&2; exit 1 ;;
    esac
  done
  local -a cmd=(gh issue close "$number" --repo "$REPO" --reason completed)
  [[ -n "$comment" ]] && cmd+=(--comment "$comment")
  "${cmd[@]}"
}
```

**Step 3: Verify the script still parses correctly**

Run: `bash -n plugins/github-project-tools/scripts/github-projects.sh`

Expected: No output (syntax OK).

**Step 4: Commit**

```bash
git add plugins/github-project-tools/scripts/github-projects.sh
git commit -m "feat(github-project-tools): add --comment flag to issue-close"
```

---

### Task 2: Add summary generation phase to end-implementation SKILL.md

**Files:**
- Modify: `plugins/github-project-tools/skills/end-implementation/SKILL.md`

**Step 1: Insert Phase 2.5 between Phase 2 and Phase 3**

Add the following new section after Phase 2 (Fetch Issue) and before Phase 3 (Set End State):

```markdown
## Phase 2.5: Generate Implementation Summary

This phase adds a closing comment summarizing what was implemented. The summary provides context for future Claude sessions reviewing this issue.

**This phase only runs when there is implementation context in the conversation** (i.e., handoff from `start-implementation` where actual implementation work was done in this session). If this skill was invoked standalone with no prior implementation context, **skip this phase entirely** — close the issue without a comment.

1. Review the conversation context: what was discussed, built, changed, and committed during this session.

2. Generate a concise summary in this format:

   ```markdown
   ## Implementation Summary

   - <what was done, 3-7 bullets>
   ```

   Each bullet should describe a concrete change (e.g., "Added `--comment` flag to `issue-close` subcommand in `github-projects.sh`"). Focus on what changed, not why.

3. Present the summary to the user: "Here's the implementation summary that will be posted as a closing comment:" followed by the formatted summary.

4. Ask the user to approve: **"Post this summary as a closing comment?"**
   - **If yes:** Save the summary text as `SUMMARY` for use in Phase 3.
   - **If no / skip:** Set `SUMMARY` to empty. The issue will be closed without a comment.
```

**Step 2: Modify the issue-close call in Phase 3, step 2**

Change the existing Phase 3 step 2 from:
```markdown
2. Close the issue:
   ```bash
   scripts/github-projects.sh issue-close <number>
   ```
```

To:
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

**Step 3: Verify the SKILL.md is well-formed**

Read through the full SKILL.md to confirm:
- Phase numbering is consistent (0, 1, 2, 2.5, 3)
- The handoff mode note at the top still makes sense
- No broken cross-references

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): add implementation summary to end-implementation"
```

---

### Task 3: Verify and bump version

**Step 1: Read the full modified SKILL.md one more time to verify correctness**

Read: `plugins/github-project-tools/skills/end-implementation/SKILL.md`

Confirm Phase 2.5 reads naturally and the Phase 3 close instructions are clear.

**Step 2: Bump the plugin version**

Read: `plugins/github-project-tools/.claude-plugin/plugin.json`
Read: `.claude-plugin/marketplace.json`

Bump the `github-project-tools` version from `0.8.1` to `0.9.0` (minor bump — new feature) in both files. Also bump `metadata.version` in marketplace.json.

**Step 3: Commit the version bump**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v0.9.0: add implementation summary to end-implementation"
```

**Step 4: Tag and push**

```bash
git tag github-project-tools/v0.9.0
```

Do NOT push — leave that for the user.
