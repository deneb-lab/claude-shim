# Mass-Update Skill Design

GitHub issue: https://github.com/elahti/deneb-marketplace/issues/73

## Summary

New `mass-update` skill for the `github-project-tools` plugin. Updates an issue and all its sub-issues on the GitHub project board: status, dates, and close state.

## Invocation

```
/github-project-tools:mass-update https://github.com/owner/repo/issues/73 todo
```

Arguments:
- Issue URL or number (required)
- Logical state hint: `todo`, `in-progress`, or `done` (optional, used for auto-detection)

## New CLI Subcommands

Three new subcommands added to `cli.py`:

| Subcommand | Args | Returns |
|---|---|---|
| `list-sub-issues <node_id>` | Issue node ID | JSON array: `[{id, number, title, state}, ...]` |
| `list-status-options` | (none, uses config) | JSON array: `[{name, id}, ...]` from the project's Status field |
| `set-status-by-option-id <item_id> <option_id>` | Project item ID + raw option ID | (void, sets the status) |

## Skill Flow

### Phase 0: Preflight

Same as existing skills. Uses shared `preflight.md` prompt.

### Phase 1: Setup

Same as existing skills. Uses shared `setup.md` prompt. Reads config, resolves `REPO_OVERRIDE`.

### Phase 2: Fetch Issue & Sub-issues

1. Parse issue arg via shared `parse-issue-arg.md`.
2. Fetch issue via `issue-view-full <number>`.
3. Verify issue is open.
4. Fetch sub-issues via `list-sub-issues <NODE_ID>`.
5. Display issue title + count of sub-issues to the user.

### Phase 3: Determine Target Status (requires user confirmation)

**User confirmation is mandatory. Never skip the prompt.**

1. If user provided a logical state arg (todo/in-progress/done):
   - Look up the default status name from config for that logical state.
   - Present as the suggested default.
2. If no logical state arg provided:
   - No auto-detection. Ask the user to pick or type a status.
3. Always prompt the user:
   - "Set status to `<auto-detected>`?" with options:
     a. Use suggested status (default)
     b. Provide a custom status name
4. If custom name provided:
   - Fetch available options via `list-status-options`.
   - Verify the name matches an available option (case-insensitive).
   - If no match, show available options and ask again.
5. Save resolved `OPTION_ID` and `LOGICAL_STATE` (null if custom status doesn't map to a logical state).

### Phase 4: Determine Date Handling (requires user confirmation)

**User confirmation is mandatory. Never skip the prompt.**

Only applies when the resolved logical state is "todo" or "done":
- For "todo": ask about setting **start date** (today).
- For "done": ask about setting **end date** (today).

Present options:
1. Set date on parent issue only
2. Set date on parent and sub-issues
3. Set date on sub-issues only
4. Do not set dates

**Important:** Never overwrite an existing date. If an issue already has the relevant date set, skip it silently.

If the logical state is "in-progress" or null (custom status), skip date handling entirely.

### Phase 5: Determine Close Handling (requires user confirmation)

**User confirmation is mandatory. Never skip the prompt.**

Only applies when the resolved logical state is "done":
- Ask: "Close the issue and all sub-issues?"
- Require explicit yes/no confirmation before proceeding.

If logical state is not "done", skip close handling.

### Phase 6: Execute Updates

Order: **sub-issues first, then parent.**

For each issue (sub-issues, then parent):
1. Check if on project board via `get-project-item <NODE_ID>`.
   - If not on board: `add-to-project <NODE_ID>` to get `ITEM_ID`.
2. Set status via `set-status-by-option-id <ITEM_ID> <OPTION_ID>`.
3. If date handling applies:
   - Check current date via `get-start-date` (for start) or equivalent (for end).
   - If date is null, set it via `set-date <ITEM_ID> <FIELD_ID>`.
4. If close handling applies:
   - Close via `issue-close <number>`.
5. Report progress: "Updated sub-issue #X: status set to Y".

After all updates, display summary.

## Shared Prompts

Copies from existing skills (per CLAUDE.md convention):
- `preflight.md`
- `conventions.md`
- `setup.md`
- `parse-issue-arg.md`

## File Changes

### New files
- `plugins/github-project-tools/skills/mass-update/SKILL.md`
- `plugins/github-project-tools/skills/mass-update/prompts/preflight.md` (copy)
- `plugins/github-project-tools/skills/mass-update/prompts/conventions.md` (copy)
- `plugins/github-project-tools/skills/mass-update/prompts/setup.md` (copy)
- `plugins/github-project-tools/skills/mass-update/prompts/parse-issue-arg.md` (copy)

### Modified files
- `plugins/github-project-tools/hook/src/github_project_tools/cli.py` — 3 new subcommands + dispatch
- `plugins/github-project-tools/hook/tests/` — tests for new subcommands
- `plugins/github-project-tools/.claude-plugin/plugin.json` — version bump
- `.claude-plugin/marketplace.json` — version bump

## Design Decisions

- **set-status-by-option-id**: Separate subcommand rather than extending `set-status`, to keep the logical-state API clean and avoid breaking existing skills.
- **list-sub-issues**: Returns id, number, title, state. Minimal but sufficient for display and operations.
- **list-status-options**: Queries the project's Status field directly. Used for validating custom status names.
- **Update order**: Sub-issues first, then parent. Prevents parent from being in a misleading state if something fails mid-way.
- **Explicit confirmation**: Phases 3, 4, and 5 always prompt the user. Never auto-proceed.
