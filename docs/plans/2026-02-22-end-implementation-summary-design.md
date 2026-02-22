# Design: Add Implementation Summary to end-implementation

## Problem

When closing an issue via end-implementation, no record of what was done is left on the issue. Future Claude sessions opening the issue see only the original description with no implementation context.

## Solution

Add a closing comment with an auto-generated implementation summary when end-implementation closes an issue.

## Approach: Extend issue-close with --comment

### Script change

Add an optional `--comment` flag to `cmd_issue_close` in `github-projects.sh`. When provided, it passes `--comment` through to `gh issue close`. Backward-compatible: omitting `--comment` works exactly as before.

### Skill change

Add a new phase to end-implementation SKILL.md between setup/fetch and the close phase:

1. **If conversation context exists** (handoff from start-implementation): Claude generates a concise bullet-point summary of what was implemented, reviewing the session's work.
2. **If no conversation context** (standalone invocation): skip the summary entirely, close without a comment.
3. Present the generated summary to the user for approval before posting.
4. Pass the approved summary as `--comment` to `issue-close`.

### Summary format

```markdown
## Implementation Summary

- <what was done, 3-7 bullets>
```

### Edge cases

- **Standalone invocation (no context):** Skip summary silently. Close without comment.
- **User declines summary:** Close without comment. Summary never blocks closing.
- **Parent issue closing:** No summary added to parent, only the child issue.

## Purpose

The summary serves future Claude sessions — providing implementation context when revisiting closed issues.

## Changes required

1. `plugins/github-project-tools/scripts/github-projects.sh` — add `--comment` to `cmd_issue_close`
2. `plugins/github-project-tools/skills/end-implementation/SKILL.md` — add summary generation phase
