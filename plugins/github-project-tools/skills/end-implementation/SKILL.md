---
name: end-implementation
description: Close a GitHub issue - sets end date, done status, closes issue, updates parent lifecycle
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *), Bash(*/github-project-tools/scripts/github-project-tools.sh count-open-sub-issues *)
---

# GitHub Projects — End Implementation

Close out a GitHub issue after implementation is complete: set the end date and done status on the project board, close the issue, and update the parent issue lifecycle if all sub-issues are resolved.

This skill works in two modes:
- **Handoff from start-implementation:** State (NODE_ID, ITEM_ID, field IDs, parent info, and REPO_OVERRIDE if set) is already in the conversation context. Phases 1 and 2 are skipped.
- **Standalone invocation:** The user calls this skill directly. All state must be discovered from scratch.

When `REPO_OVERRIDE` is set (either from start-implementation handoff or parsed from a URL in Phase 2), **prepend `--repo $REPO_OVERRIDE` before the subcommand in every script invocation** to override auto-detection.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Phase 1: Setup (conditional)

**If state from `start-implementation` is already in the conversation context** (NODE_ID, ITEM_ID, field IDs, and parent info are known), **skip to Phase 2.5.**

Otherwise, follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Fetch Issue (conditional)

**If state from `start-implementation` is already in the conversation context**, **skip to Phase 2.5.**

Otherwise:

1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).

2. Fetch the issue details:
   ```bash
   <cli> issue-view-full <number>
   ```
   Save the JSON output. Extract the issue `id` as `NODE_ID`.

3. Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is already closed and stop.

4. **If a project is available**, get the project item ID:
   ```bash
   <cli> get-project-item "$NODE_ID"
   ```
   Save the output as `ITEM_ID`.

5. Check for a parent issue:
   ```bash
   <cli> get-parent "$NODE_ID"
   ```
   If the result is not `null`, save:
   - `PARENT_ID` from `.id`
   - `PARENT_NUMBER` from `.number`
   - `PARENT_TITLE` from `.title`

## Phase 2.5: Generate Implementation Summary

This phase adds a closing comment summarizing what was implemented. The summary provides context for future Claude sessions reviewing this issue.

**This phase only runs when there is implementation context in the conversation** (i.e., handoff from `start-implementation` where actual implementation work was done in this session). If this skill was invoked standalone with no prior implementation context, **skip this phase entirely** — close the issue without a comment.

1. Review the conversation context: what was discussed, built, changed, and committed during this session.

2. Generate a concise summary in this format:

   ```markdown
   ## Implementation Summary

   - <what was done, 3-7 bullets>
   ```

   Each bullet should describe a concrete change (e.g., "Added `--comment` flag to `issue-close` subcommand in `cli.py`"). Focus on what changed, not why.

3. Present the summary to the user: "Here's the implementation summary that will be posted as a closing comment:" followed by the formatted summary.

4. Ask the user to approve: **"Post this summary as a closing comment?"**
   - **If yes:** Save the summary text as `SUMMARY` for use in Phase 3.
   - **If no / skip:** Set `SUMMARY` to empty. The issue will be closed without a comment.

## Phase 3: Set End State

1. **If a project is available:**

   a. Set the end date to today:
      ```bash
      <cli> set-date "$ITEM_ID" "$END_FIELD"
      ```

   b. Set status to done:
      ```bash
      <cli> set-status "$ITEM_ID" done
      ```

2. Close the issue. If `SUMMARY` is non-empty (from Phase 2.5), include it as a closing comment:
   ```bash
   <cli> issue-close <number> --comment "SUMMARY"
   ```
   If `SUMMARY` is empty, close without a comment:
   ```bash
   <cli> issue-close <number>
   ```

3. **If a parent issue exists** (regardless of whether a project is available):

   a. Count open sub-issues on the parent:
      ```bash
      <cli> count-open-sub-issues "$PARENT_ID"
      ```

   b. If the count is **0** (all sub-issues are now resolved):
      - **Ask the user:** "All sub-issues resolved. Close parent #PARENT_NUMBER (PARENT_TITLE)?"
      - **Only proceed if the user confirms.**
      - If confirmed **and a project is available**:

        Get the parent's project item ID:
        ```bash
        <cli> get-project-item "$PARENT_ID"
        ```
        Save the output as `PARENT_ITEM`.

        Set the parent's end date to today:
        ```bash
        <cli> set-date "$PARENT_ITEM" "$END_FIELD"
        ```

        Set the parent's status to done:
        ```bash
        <cli> set-status "$PARENT_ITEM" done
        ```

      - If confirmed, close the parent issue (regardless of whether a project is available):
        ```bash
        <cli> issue-close <parent_number>
        ```

      - If the user declines, leave the parent as-is.

4. Tell the user the issue is implemented and closed.

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
