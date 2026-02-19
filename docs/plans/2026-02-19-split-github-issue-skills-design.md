# Split github-implement-issue into start/end-implementation

## Summary

Split the monolithic `github:implement-issue` skill into two independent skills (`github-projects:start-implementation` and `github-projects:end-implementation`). Rename all skill prefixes from `github:` to `github-projects:`. Add three new subcommands to `github-projects.sh`.

## Approach

**Clean split with shared state convention.** Each skill is self-contained and works standalone. When `start-implementation` hands off to `end-implementation` via the Skill tool, state (NODE_ID, ITEM_ID, field IDs, parent info) carries through the conversation context. When `end-implementation` is invoked standalone, it re-discovers everything from scratch.

## File Changes

### New files

- `plugins/github-project-tools/skills/github-projects-start-implementation/SKILL.md`
- `plugins/github-project-tools/skills/github-projects-end-implementation/SKILL.md`

### Modified files

- `plugins/github-project-tools/scripts/github-projects.sh` — add `preflight`, `issue-assign`, `pr-create-draft` subcommands
- `plugins/github-project-tools/skills/github-add-issue/SKILL.md` — rename `github:add-issue` to `github-projects:add-issue`
- `plugins/github-project-tools/.claude-plugin/plugin.json` — version bump
- `.claude-plugin/marketplace.json` — version bump

### Deleted files

- `plugins/github-project-tools/skills/github-implement-issue/SKILL.md`

### Renamed directories

- `github-add-issue/` → `github-projects-add-issue/`

## Skill: github-projects:start-implementation

```yaml
---
name: github-projects:start-implementation
description: Start implementing a GitHub issue - assigns, sets dates/status, creates draft PR, and presents issue context
---
```

### Phase 0: Preflight

1. Find bundled script at `~/.claude/plugins/**/github-project-tools/scripts/github-projects.sh`
2. Run `scripts/github-projects.sh preflight`
3. Stop with clear message if preflight fails

### Phase 1: Setup

1. Auto-detect repo, project (may be none), fields, statuses via script init
2. Claude maps detected status options to `todo` / `in-progress` / `done`
3. If no project detected: skip all project operations in later phases

### Phase 2: Fetch Issue

1. Parse argument — extract issue number from plain `42` or `https://github.com/owner/repo/issues/42`
2. `scripts/github-projects.sh issue-view <number> --json id,number,title,body,state`
3. Verify `state == OPEN`. If closed, tell user and stop.
4. Save `NODE_ID` from `.id`
5. `scripts/github-projects.sh get-parent "$NODE_ID"`
6. If parent exists: save `PARENT_ID`, `PARENT_NUMBER`

### Phase 3: Set Start State

1. `scripts/github-projects.sh issue-assign <number>`
2. If project:
   - `scripts/github-projects.sh get-project-item "$NODE_ID"` — if empty, `add-to-project "$NODE_ID"` first
   - Save result as `ITEM_ID`
   - `scripts/github-projects.sh set-date "$ITEM_ID" "$START_FIELD" "$(date +%Y-%m-%d)"`
   - `scripts/github-projects.sh set-status "$ITEM_ID" in-progress`
3. If parent exists + project:
   - `scripts/github-projects.sh get-start-date "$PARENT_ID"`
   - Save `PARENT_ITEM` from `.item_id` and `PARENT_DATE` from `.date`
   - If `PARENT_DATE` is `"null"`: ask user "Parent #X has no start date. Set start date to today and status to in-progress?"
   - Only proceed if user confirms
4. Ask user: "Create a draft PR linked to this issue?"
   - If yes: `scripts/github-projects.sh pr-create-draft <number>`

### Phase 4: Implement

1. Present issue title + body to the user
2. Follow user's additional instructions

### Phase 5: Handoff

1. Ask: "Implementation complete. Run end-implementation to close the issue?"
2. If yes → invoke `github-projects:end-implementation` via Skill tool (state stays in context)
3. If no → tell user to run `/github-projects:end-implementation` later
4. If can't implement → present options:
   - **Option A: Do nothing** — leave current state as-is
   - **Option B: Reset** — restore issue (and parent, if touched) to their original status before this skill ran

## Skill: github-projects:end-implementation

```yaml
---
name: github-projects:end-implementation
description: Close a GitHub issue - sets end date, done status, closes issue, updates parent lifecycle
---
```

### Phase 0: Preflight

1. Find bundled script
2. `scripts/github-projects.sh preflight`
3. Stop if fails

### Phase 1: Setup (conditional)

1. If state from `start-implementation` already in context (NODE_ID, ITEM_ID, field IDs, parent info are known) → skip to Phase 3
2. Otherwise: auto-detect repo, project, fields, statuses

### Phase 2: Fetch Issue (conditional)

1. If state already in context → skip to Phase 3
2. Otherwise:
   - Parse issue number/URL from argument
   - `scripts/github-projects.sh issue-view <number> --json id,number,title,body,state`
   - `scripts/github-projects.sh get-project-item "$NODE_ID"` → save `ITEM_ID`
   - `scripts/github-projects.sh get-parent "$NODE_ID"` → save `PARENT_ID`, `PARENT_NUMBER` if exists

### Phase 3: Set End State

1. If project:
   - `scripts/github-projects.sh set-date "$ITEM_ID" "$END_FIELD" "$(date +%Y-%m-%d)"`
   - `scripts/github-projects.sh set-status "$ITEM_ID" done`
2. `scripts/github-projects.sh issue-close <number>`
3. If parent exists + project:
   - `scripts/github-projects.sh count-open-sub-issues "$PARENT_ID"`
   - If count is 0: ask user "All sub-issues resolved. Close parent #X?"
   - If user confirms:
     - `scripts/github-projects.sh get-project-item "$PARENT_ID"` → save `PARENT_ITEM`
     - `scripts/github-projects.sh set-date "$PARENT_ITEM" "$END_FIELD" "$(date +%Y-%m-%d)"`
     - `scripts/github-projects.sh set-status "$PARENT_ITEM" done`
     - `scripts/github-projects.sh issue-close <parent_number>`
   - If user declines: leave parent as-is
4. Tell the user the issue is implemented and closed.

## Skill: github-projects:add-issue (rename only)

Rename frontmatter `name` from `github:add-issue` to `github-projects:add-issue`. Rename directory from `github-add-issue` to `github-projects-add-issue`. No logic changes.

## Script Changes: github-projects.sh

### New subcommands

| Subcommand | Implementation |
|---|---|
| `preflight` | Verify `gh --version` exists, run `gh auth status`, check `repo` and `project` scopes are present. Exit non-zero with clear message on failure. |
| `issue-assign <number>` | `gh issue edit <number> --add-assignee @me` |
| `pr-create-draft <number>` | `gh pr create --draft` — title from issue, body `Closes #<number>` |

### Unchanged

All existing subcommands (`issue-view`, `issue-create`, `issue-edit`, `issue-close`, `get-project-item`, `get-project-fields`, `get-start-date`, `add-to-project`, `set-status`, `set-date`, `get-parent`, `count-open-sub-issues`, `table-set-status`). Auto-detection functions (`detect_repo`, `detect_project`, `detect_status_field`, `init`) unchanged. Deneb override (`phoebe.fi.*dotfiles → elahti/deneb`) unchanged.

## Important Notes

- All bash commands start with the script — never wrap in variable assignments
- JSON processing: extract values in-context, no separate `echo | jq`
- All GitHub operations go through `scripts/github-projects.sh` — never call `gh` directly
- Action Plan table operations (`table-set-status`) remain in the script but are not used by these skills — they are for trivy-audit
- Date field IDs looked up at runtime — may change if project is recreated
