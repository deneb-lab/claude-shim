---
name: mass-update-issues
description: Update an issue and all its sub-issues - sets status, dates, and close state on the project board
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh repo-detect), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh list-sub-issues *), Bash(*/github-project-tools/scripts/github-project-tools.sh list-status-options *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status-by-option-id *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *)
---

# GitHub Projects — Mass Update

Update an issue and all its sub-issues on the project board: set status, dates, and optionally close them.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Phase 1: Setup

Follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Fetch Issue & Sub-issues

1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).

   **Important:** The user may also provide a logical state hint after the issue number/URL (e.g., `73 todo` or `https://...issues/73 done`). Extract and save this as `STATE_HINT` if present. Valid hints are: `todo`, `in-progress`, `done`. Anything else is not a hint — ignore it.

2. Fetch the issue details:
   ```bash
   <cli> issue-view-full <number>
   ```
   Save the JSON output. Extract the issue `id` as `NODE_ID`, `title`, `body`, and `state`.

3. Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is closed and stop.

4. Fetch sub-issues:
   ```bash
   <cli> list-sub-issues "$NODE_ID"
   ```
   Save the JSON array as `SUB_ISSUES`. Each element has `id`, `number`, `title`, `state`.

5. Display to the user:
   ```
   Issue #<number>: <title>
   Found <count> sub-issues:
   - #<sub_number>: <sub_title> (<sub_state>)
   - ...
   ```

   If there are no sub-issues, tell the user and continue (the skill can still update the parent issue alone).

## Phase 3: Determine Target Status

**User confirmation is MANDATORY. NEVER skip the prompt, even if a state hint was provided.**

1. Read the config's status field to understand available logical states and their default mappings.

2. **If `STATE_HINT` is set** (todo, in-progress, or done):
   - Look up the default status mapping from config for that logical state.
   - Extract the `name` and `option-id` as the suggested status.
   - Save `STATE_HINT` as `LOGICAL_STATE`.

3. **If `STATE_HINT` is not set:**
   - No auto-detection. `LOGICAL_STATE` is null.

4. **Always prompt the user using AskUserQuestion.** Present options:
   - If a suggestion was auto-detected: "Use `<suggested_name>` (from `<LOGICAL_STATE>` state)" as the first/default option.
   - "Provide a custom status name" as another option.
   - If no suggestion: only show "Provide a custom status name" and list the logical states (todo, in-progress, done) as options too.

5. **If the user provides a custom status name:**
   a. Fetch all available status options:
      ```bash
      <cli> list-status-options
      ```
   b. Match the user-provided name against the returned options (case-insensitive).
   c. If a match is found: save the matching `id` as `OPTION_ID`. Check if this option ID matches any logical state's default in the config. If it does, set `LOGICAL_STATE` to that state. Otherwise, `LOGICAL_STATE` is null.
   d. If no match: show the available status options and ask the user again. Repeat until a valid status is confirmed.

6. **If the user selected the auto-detected suggestion:**
   - Save the option-id from config as `OPTION_ID`.

7. Confirm the final choice: "Will set status to `<name>` (option ID: `<OPTION_ID>`) on #<number> and <count> sub-issues. Proceed?"
   - **Wait for explicit confirmation before continuing.**

## Phase 4: Determine Date Handling

**User confirmation is MANDATORY. NEVER skip the prompt.**

This phase only applies when `LOGICAL_STATE` is `"todo"` or `"done"`. If `LOGICAL_STATE` is `"in-progress"` or null, **skip this phase entirely** but **tell the user** you're skipping it: "Skipping date handling (not applicable for `<status>` status)."

1. Determine which date field applies:
   - `"todo"` → start date (`START_FIELD`)
   - `"done"` → end date (`END_FIELD`)

2. **Prompt the user using AskUserQuestion:**
   - For "todo": "Set **start date** (today) on which issues?"
   - For "done": "Set **end date** (today) on which issues?"

   Options:
   a. Set date on parent issue only
   b. Set date on parent and sub-issues (Recommended)
   c. Set date on sub-issues only
   d. Do not set dates

3. Save the user's choice as `DATE_SCOPE` (one of: `parent-only`, `parent-and-subs`, `subs-only`, `none`).

4. **Important rule:** When executing date updates in Phase 6, **never overwrite an existing date**. Check each issue's current date before setting. If a date is already set, skip that issue silently.

## Phase 5: Determine Close Handling

**User confirmation is MANDATORY. NEVER skip the prompt.**

This phase only applies when `LOGICAL_STATE` is `"done"`. If `LOGICAL_STATE` is not `"done"`, **skip this phase entirely** but **tell the user** you're skipping it: "Skipping close handling (not applicable for `<status>` status)."

1. **Prompt the user using AskUserQuestion:**
   "Close #<number> and all its sub-issues?"

   Options:
   a. Yes, close all
   b. No, only update status and dates

2. Save the user's choice as `CLOSE_ISSUES` (boolean).

## Phase 6: Execute Updates

**Order: sub-issues first, then parent.**

For each issue in the update list (all sub-issues, then the parent issue):

1. **Ensure issue is on the project board:**
   ```bash
   <cli> get-project-item "$ISSUE_NODE_ID"
   ```
   - If the output is **non-empty**: save as `ISSUE_ITEM_ID`.
   - If the output is **empty**: add to project:
     ```bash
     <cli> add-to-project "$ISSUE_NODE_ID"
     ```
     Save the output as `ISSUE_ITEM_ID`.

2. **Set status:**
   ```bash
   <cli> set-status-by-option-id "$ISSUE_ITEM_ID" "$OPTION_ID"
   ```

3. **Set date** (if `DATE_SCOPE` applies to this issue):
   - Determine if this issue is in scope based on `DATE_SCOPE`:
     - `parent-only`: only the parent issue
     - `parent-and-subs`: all issues
     - `subs-only`: only sub-issues
     - `none`: skip all
   - If in scope, check current date:
     ```bash
     <cli> get-start-date "$ISSUE_NODE_ID"
     ```
     Extract the date. If it is `null` (no date set), set it:
     ```bash
     <cli> set-date "$ISSUE_ITEM_ID" "$DATE_FIELD_ID"
     ```
     If a date is already set, skip silently.

     Note: `get-start-date` checks the start date field. For end dates, there is no `get-end-date` subcommand. For end dates, use the same `get-start-date` logic but note it only checks start dates. Since `set-date` accepts any field ID, pass `END_FIELD` for done states. To check existing end dates, query the project item's field values — but since there's no dedicated subcommand, **always set end dates** (the GraphQL mutation is idempotent — setting the same date again is harmless).

4. **Close issue** (if `CLOSE_ISSUES` is true):
   ```bash
   <cli> issue-close <issue_number>
   ```

5. **Report progress** after each issue:
   ```
   Updated #<number> (<title>): status → <status_name>
   ```

After all updates complete, display a summary:
```
Mass update complete:
- Status: <status_name>
- Issues updated: <count>
- Dates set: <count> (or "skipped")
- Issues closed: <count> (or "skipped")
```

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).

Additional conventions for this skill:
- **Explicit confirmation is mandatory** for Phases 3, 4, and 5. Never auto-proceed. Always use AskUserQuestion.
- **Sub-issues first, then parent.** This prevents the parent from being in a misleading state if something fails mid-way.
- **Never overwrite existing dates.** Check before setting.
- **Project is required** for this skill. If no project config is available during setup, tell the user: "mass-update-issues requires a configured project board. Run setup first." and stop.
