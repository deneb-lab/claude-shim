# Design: Set Owner on Parent Issue During start-implementation

**Issue:** #5
**Date:** 2026-02-20

## Problem

When starting implementation on a sub-issue, the parent issue doesn't reflect the user's involvement. The `start-implementation` skill assigns the user to the child issue but ignores the parent.

## Solution

Add an unconditional `issue-assign` call for the parent issue in Phase 3 of `start-implementation/SKILL.md`, right after assigning the child issue.

### Approach: Skill-only change

The existing `issue-assign` subcommand (`gh issue edit <number> --add-assignee @me`) is idempotent -- no error if already assigned. No script changes needed.

### Change location

`plugins/github-project-tools/skills/start-implementation/SKILL.md`, Phase 3, new step between current step 1 (assign issue) and step 2 (project operations):

```
If a parent issue exists (detected in Phase 2):
  scripts/github-projects.sh issue-assign <parent_number>
```

### Edge cases

- **No parent:** Step skipped (conditional on parent existing)
- **Already assigned:** `--add-assignee @me` is a no-op
- **Parent is closed:** GitHub allows adding assignees to closed issues
- **Cross-repo parent:** Not applicable; GitHub sub-issues are same-repo

### Alternatives considered

- **New script subcommand** (`issue-assign-parent`): Over-engineered, skill already knows the parent number
- **Generalize issue-assign for multiple issues:** Unnecessary interface change
