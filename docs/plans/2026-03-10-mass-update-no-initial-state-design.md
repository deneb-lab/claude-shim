# Mass-Update Skill: Remove Initial State Requirement

## Problem

The mass-update skill currently requires the parent issue to be OPEN. It should work regardless of the initial state of the parent issue or any sub-issue.

## Design

### CLI Changes

**New subcommand: `clear-date`**
```
<cli> clear-date <item_id> <field_id>
```
Clears a date field on a project item by setting it to null via GraphQL. Includes the same field type validation as `set-date`.

**New subcommand: `reopen-issue`**
```
<cli> reopen-issue <number>
```
Reopens a closed GitHub issue.

### Skill Flow Changes

**Phase 2** — Remove the "verify issue is OPEN" gate. Save `PARENT_STATE` (OPEN/CLOSED) for later logic.

**Phase 3** — When target status maps to no logical state (custom), ask the user whether sub-issues should also be updated.

**Phases 4+5 replaced by unified Phase 4** — Determine update scope from logical state and parent state. No per-aspect user prompts; behavior is deterministic.

**Phase 6 rewritten as Phase 5** — Execute with new logic, single confirmation before execution.

### Update Scope by Logical State

| Target | Parent open | Parent closed |
|---|---|---|
| **done** | Status + end-date + close on parent AND all subs | Status + end-date + close on parent AND all subs |
| **todo** | Status + clear start & end dates on parent AND all subs | Reopen parent. Status + clear start & end dates on parent only |
| **in-progress** | Status + start-date (if missing) + clear end-date on parent only | Reopen parent. Status + start-date (if missing) + clear end-date on parent only |
| **custom** | Status on parent. Subs only if user said yes | Status on parent. Subs only if user said yes |

### Execution Order Per Issue

1. Ensure on project board (`get-project-item` → `add-to-project` if needed)
2. Set status (`set-status-by-option-id`)
3. Date operations per logical state:
   - **done**: `set-date <item_id> <end_field>`
   - **todo**: `clear-date <item_id> <start_field>`, `clear-date <item_id> <end_field>`
   - **in-progress**: if start date null → `set-date <item_id> <start_field>`, then `clear-date <item_id> <end_field>`
   - **custom**: no-op
4. Open/close:
   - **done**: `issue-close <number>` on all updated issues
   - **todo/in-progress**: `reopen-issue <number>` on parent only (if closed)
   - **custom**: no-op

Sub-issues are processed before the parent.

### Confirmation Prompt

Single confirmation before execution:
```
Will update #89 and 3 sub-issues:
- Status: Done
- End date: 2026-03-10
- Close: yes
Proceed?
```

### Files Changed

- `plugins/github-project-tools/hook/src/github_project_tools/cli.py` — add `clear-date`, `reopen-issue`
- `plugins/github-project-tools/hook/tests/test_cli.py` — tests for new subcommands
- `plugins/github-project-tools/scripts/github-project-tools.sh` — route new subcommands
- `plugins/github-project-tools/skills/mass-update-issues/SKILL.md` — rewrite phases
- No changes to shared prompts (`preflight.md`, `setup.md`, `parse-issue-arg.md`, `conventions.md`)
