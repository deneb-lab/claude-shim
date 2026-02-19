---
name: end-implementation
description: Close a GitHub issue - sets end date, done status, closes issue, updates parent lifecycle
---

# GitHub Projects — End Implementation

Close out a GitHub issue after implementation is complete: set the end date and done status on the project board, close the issue, and update the parent issue lifecycle if all sub-issues are resolved.

This skill works in two modes:
- **Handoff from start-implementation:** State (NODE_ID, ITEM_ID, field IDs, parent info) is already in the conversation context. Phases 1 and 2 are skipped.
- **Standalone invocation:** The user calls this skill directly. All state must be discovered from scratch.

## Phase 0: Preflight

1. Find the bundled script at `~/.claude/plugins/**/github-project-tools/scripts/github-projects.sh`
2. Run preflight checks:
   ```bash
   scripts/github-projects.sh preflight
   ```
3. If preflight fails, stop and show the error message to the user. Do not proceed.

## Phase 1: Setup (conditional)

**If state from `start-implementation` is already in the conversation context** (NODE_ID, ITEM_ID, field IDs, and parent info are known), **skip to Phase 3.**

Otherwise, discover everything from scratch:

1. Get project fields (date field IDs):
   ```bash
   scripts/github-projects.sh get-project-fields
   ```
   This returns JSON with `start` and `end` field IDs. Save these as `START_FIELD` and `END_FIELD`.

   If this command fails because no project is found, note that **no project is available**. Skip all project operations (get-project-item, set-date, set-status) in later phases. Continue with issue-only operations.

2. The `set-status` subcommand accepts the literal arguments `todo`, `in-progress`, and `done` directly — no manual mapping of project-specific status names is needed.

## Phase 2: Fetch Issue (conditional)

**If state from `start-implementation` is already in the conversation context**, **skip to Phase 3.**

Otherwise:

1. Parse the argument. The user provides either:
   - A plain issue number like `42`
   - A full GitHub URL like `https://github.com/owner/repo/issues/42`

   Extract the issue number from whichever format is provided.

2. Fetch the issue details:
   ```bash
   scripts/github-projects.sh issue-view <number> --json id,number,title,body,state
   ```
   Save the JSON output. Extract the issue `id` as `NODE_ID`.

3. Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is already closed and stop.

4. **If a project is available**, get the project item ID:
   ```bash
   scripts/github-projects.sh get-project-item "$NODE_ID"
   ```
   Save the output as `ITEM_ID`.

5. Check for a parent issue:
   ```bash
   scripts/github-projects.sh get-parent "$NODE_ID"
   ```
   If the result is not `null`, save:
   - `PARENT_ID` from `.id`
   - `PARENT_NUMBER` from `.number`
   - `PARENT_TITLE` from `.title`

## Phase 3: Set End State

1. **If a project is available:**

   a. Set the end date to today:
      ```bash
      scripts/github-projects.sh set-date "$ITEM_ID" "$END_FIELD" "$(date +%Y-%m-%d)"
      ```

   b. Set status to done:
      ```bash
      scripts/github-projects.sh set-status "$ITEM_ID" done
      ```

2. Close the issue:
   ```bash
   scripts/github-projects.sh issue-close <number>
   ```

3. **If a parent issue exists** (regardless of whether a project is available):

   a. Count open sub-issues on the parent:
      ```bash
      scripts/github-projects.sh count-open-sub-issues "$PARENT_ID"
      ```

   b. If the count is **0** (all sub-issues are now resolved):
      - **Ask the user:** "All sub-issues resolved. Close parent #PARENT_NUMBER (PARENT_TITLE)?"
      - **Only proceed if the user confirms.**
      - If confirmed **and a project is available**:

        Get the parent's project item ID:
        ```bash
        scripts/github-projects.sh get-project-item "$PARENT_ID"
        ```
        Save the output as `PARENT_ITEM`.

        Set the parent's end date to today:
        ```bash
        scripts/github-projects.sh set-date "$PARENT_ITEM" "$END_FIELD" "$(date +%Y-%m-%d)"
        ```

        Set the parent's status to done:
        ```bash
        scripts/github-projects.sh set-status "$PARENT_ITEM" done
        ```

      - If confirmed, close the parent issue (regardless of whether a project is available):
        ```bash
        scripts/github-projects.sh issue-close <parent_number>
        ```

      - If the user declines, leave the parent as-is.

4. Tell the user the issue is implemented and closed.

## Important Notes

- **All bash commands** must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `scripts/github-projects.sh` — never call `gh` directly.
- **Date field IDs** are looked up at runtime via `get-project-fields` — they may change if the project is recreated.
- **Project is optional.** If no project is detected in Phase 1, skip all project operations (get-project-item, set-date, set-status) but still perform issue operations (close, parent check, parent close).
