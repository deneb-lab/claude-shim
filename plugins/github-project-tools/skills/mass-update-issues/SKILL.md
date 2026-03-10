---
name: mass-update-issues
description: Update an issue and all its sub-issues - sets status, dates, and close state on the project board
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh repo-detect), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh list-sub-issues *), Bash(*/github-project-tools/scripts/github-project-tools.sh list-status-options *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status-by-option-id *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh clear-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *), Bash(*/github-project-tools/scripts/github-project-tools.sh reopen-issue *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *)
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

3. Save `state` as `PARENT_STATE` (either `OPEN` or `CLOSED`). Do **not** reject closed issues.

4. Fetch sub-issues:
   ```bash
   <cli> list-sub-issues "$NODE_ID"
   ```
   Save the JSON array as `SUB_ISSUES`. Each element has `id`, `number`, `title`, `state`.

5. Display to the user:
   ```
   Issue #<number>: <title> (<PARENT_STATE>)
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

7. **If `LOGICAL_STATE` is null** (custom status with no logical mapping):
   - Ask the user: "Should sub-issues also be updated to `<status_name>`?"
   - Save the answer as `UPDATE_SUBS` (boolean).

8. Determine the update scope based on `LOGICAL_STATE` and `PARENT_STATE`:

   | Target | Parent OPEN | Parent CLOSED |
   |---|---|---|
   | **done** | Status + end-date + close on parent AND all subs | Status + end-date + close on parent AND all subs |
   | **todo** | Status + clear start & end dates on parent AND all subs | Reopen parent. Status + clear start & end dates on parent only |
   | **in-progress** | Status + start-date (if missing) + clear end-date on parent only | Reopen parent. Status + start-date (if missing) + clear end-date on parent only |
   | **custom (null)** | Status on parent. Subs only if `UPDATE_SUBS` is true | Status on parent. Subs only if `UPDATE_SUBS` is true |

9. Confirm the final choice. Summarize all planned actions:
   ```
   Will update #<number> (and <count> sub-issues):
   - Status: <status_name>
   - Dates: <what will happen with dates, or "no changes">
   - Open/close: <what will happen, or "no changes">
   Proceed?
   ```
   - **Wait for explicit confirmation before continuing.**

## Phase 4: Execute Updates

**Order: sub-issues first, then parent.**

Determine which issues to update:
- **done**: parent and all sub-issues.
- **todo**: parent and all sub-issues if `PARENT_STATE` was `OPEN`; parent only if `PARENT_STATE` was `CLOSED`.
- **in-progress**: parent only.
- **custom (null)**: parent always; sub-issues only if `UPDATE_SUBS` is true.

For each issue in the update list (sub-issues first, then the parent):

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

3. **Date operations** (based on `LOGICAL_STATE`):

   - **done**: Set end date:
     ```bash
     <cli> set-date "$ISSUE_ITEM_ID" "$END_FIELD"
     ```

   - **todo**: Clear start and end dates:
     ```bash
     <cli> clear-date "$ISSUE_ITEM_ID" "$START_FIELD"
     <cli> clear-date "$ISSUE_ITEM_ID" "$END_FIELD"
     ```

   - **in-progress**: Check start date, set if missing. Clear end date:
     ```bash
     <cli> get-start-date "$ISSUE_NODE_ID"
     ```
     If the date is `null`, set it:
     ```bash
     <cli> set-date "$ISSUE_ITEM_ID" "$START_FIELD"
     ```
     Then clear end date:
     ```bash
     <cli> clear-date "$ISSUE_ITEM_ID" "$END_FIELD"
     ```

   - **custom (null)**: No date operations.

4. **Open/Close** (based on `LOGICAL_STATE`):

   - **done**: Close the issue:
     ```bash
     <cli> issue-close <issue_number>
     ```

   - **todo** or **in-progress**: Reopen **only the parent** (if `PARENT_STATE` was `CLOSED` and this is the parent issue):
     ```bash
     <cli> reopen-issue <parent_number>
     ```
     Do **not** reopen sub-issues.

   - **custom (null)**: No open/close operations.

5. **Report progress** after each issue:
   ```
   Updated #<number> (<title>): status → <status_name>
   ```

After all updates complete, display a summary:
```
Mass update complete:
- Status: <status_name>
- Issues updated: <count>
- Dates set/cleared: <count> (or "skipped")
- Issues closed: <count> (or "skipped")
- Issues reopened: <count> (or "skipped")
```

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).

Additional conventions for this skill:
- **Explicit confirmation is mandatory** for Phase 3. Never auto-proceed. Always use AskUserQuestion.
- **Sub-issues first, then parent.** This prevents the parent from being in a misleading state if something fails mid-way.
- **Project is required** for this skill. If no project config is available during setup, tell the user: "mass-update-issues requires a configured project board. Run setup first." and stop.
- **Do not fail on missing date fields.** If `clear-date` or `set-date` fails for an issue, log a warning and continue with the next issue.
