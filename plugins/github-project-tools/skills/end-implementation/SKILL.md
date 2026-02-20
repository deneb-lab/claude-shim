---
name: end-implementation
description: Close a GitHub issue - sets end date, done status, closes issue, updates parent lifecycle
allowed-tools: Bash(github-projects.sh:*), Bash(find:*), Bash(date:*)
---

# GitHub Projects — End Implementation

Close out a GitHub issue after implementation is complete: set the end date and done status on the project board, close the issue, and update the parent issue lifecycle if all sub-issues are resolved.

This skill works in two modes:
- **Handoff from start-implementation:** State (NODE_ID, ITEM_ID, field IDs, parent info, and REPO_OVERRIDE if set) is already in the conversation context. Phases 1 and 2 are skipped.
- **Standalone invocation:** The user calls this skill directly. All state must be discovered from scratch.

When `REPO_OVERRIDE` is set (either from start-implementation handoff or parsed from a URL in Phase 2), **prepend `--repo $REPO_OVERRIDE` before the subcommand in every script invocation** to override auto-detection.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

## Phase 1: Setup (conditional)

**If state from `start-implementation` is already in the conversation context** (NODE_ID, ITEM_ID, field IDs, and parent info are known), **skip to Phase 3.**

Otherwise, follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Fetch Issue (conditional)

**If state from `start-implementation` is already in the conversation context**, **skip to Phase 3.**

Otherwise:

1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).

2. Fetch the issue details:
   ```bash
   scripts/github-projects.sh issue-view-full <number>
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

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
