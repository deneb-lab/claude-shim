# Design: Verify End-Implementation Skill

**Date:** 2026-03-03
**Issue:** [#76](https://github.com/elahti/deneb-marketplace/issues/76) — Verify end-implementation skill

## Problem

The `end-implementation` skill is missing several workflow steps compared to the expected behavior defined in issue #76. Gaps include: no start date check, no assignment check, closing comments only in handoff mode, no parent assignment check.

## Gap Analysis

| # | Expected | Current | Status |
|---|---|---|---|
| 1 | Check start date; auto-detect from "in progress" history | Not implemented | Missing |
| 2 | Check assignment; prompt to assign if not assigned | Not implemented | Missing |
| 3 | Closing comment in both standalone and handoff mode; use git log | Only handoff mode; no git log | Partial |
| 4 | Parent assignment check | Not implemented | Missing |
| 5 | Separate parent status/end-date prompts | Combined "Close parent?" | Acceptable (keep combined) |
| 6 | No parent start date offer | Correctly not offered | OK |

## Design

### Revised Skill Workflow

```
Phase 0: Preflight (unchanged)
Phase 1: Setup (unchanged, conditional)
Phase 2: Fetch Issue (unchanged, conditional)

NEW → Phase 2.3: Pre-close checks
  2.3a. Check start date (via get-start-date on project item)
        - If missing → query get-status-change-date for "In Progress" date
        - Suggest detected date (or today as fallback)
        - Prompt: "Issue has no start date. Set to <suggested>?"
  2.3b. Check assignment (via issue-get-assignees)
        - If current user not in assignees → prompt: "Assign yourself to #N?"

REVISED → Phase 2.5: Closing comment (runs in BOTH modes)
  Handoff mode:
    - Review conversation context + git log (non-main branch)
    - Generate 3-7 bullet summary
    - Present for approval, option to skip
  Standalone mode:
    - Check git log (non-main branch)
    - Cross-check against issue title/body for relevance
    - If relevant: generate summary, present for approval
    - If not: offer manual comment or skip
  Git log is done by the agent (not a CLI subcommand).

Phase 3: Set end state
  3a. Set end date + done status (unchanged)
  3b. Close issue with optional comment (unchanged)
  3c. Parent sub-issue check (unchanged — combined prompt)
  NEW → 3d. Parent assignment check (via issue-get-assignees)
    - If not assigned → prompt: "Assign yourself to parent #P?"
  - Do NOT offer parent start date (already correct)

Phase 4: Report (unchanged)
```

### New CLI Subcommands

1. **`get-status-change-date <node_id> <status_name>`** — Query project item timeline for when status was last set to the given value. Returns date string or `null`.

2. **`issue-get-assignees <number>`** — Return JSON array of assignee logins for the issue. Uses `gh issue view <number> --json assignees`.

### CLI Subcommands to Remove

- `issue-edit` — not used by any skill
- `table-set-status` — not used by any skill

### Skill allowed-tools Additions

Add to `end-implementation` allowed-tools:
- `get-start-date *`
- `get-status-change-date *`
- `issue-get-assignees *`
- `issue-assign *`

## Decisions Made

- **Start date auto-detection:** New CLI subcommand (`get-status-change-date`) using GraphQL API, rather than simpler fallbacks.
- **Assignee check:** New CLI subcommand (`issue-get-assignees`), not extending `issue-view-full`.
- **Closing comment:** Always offered in both modes. Git log done by agent, not CLI.
- **Parent prompts:** Keep combined "Close parent?" prompt (not split into separate status/date prompts).
- **Unused CLI cleanup:** Remove `issue-edit` and `table-set-status` as part of this work.
