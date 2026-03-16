---
name: end-implementing-issue
description: Close a GitHub issue - sets end date, done status, closes issue, updates parent lifecycle
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh repo-detect), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *), Bash(*/github-project-tools/scripts/github-project-tools.sh count-open-sub-issues *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-status-change-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *), Bash(git rev-parse *), Bash(git log *)
---

# GitHub Projects — End Implementation

Close out a GitHub issue after implementation is complete: set the end date and done status on the project board, close the issue, and update the parent issue lifecycle if all sub-issues are resolved.

This skill works in two modes:
- **Handoff from start-implementing-issue:** State (NODE_ID, ITEM_ID, field IDs, parent info, and REPO_OVERRIDE if set) is already in the conversation context. Phases 1 and 2 are skipped.
- **Standalone invocation:** The user calls this skill directly. All state must be discovered from scratch.

When `REPO_OVERRIDE` is set (either from start-implementing-issue handoff or parsed from a URL in Phase 2), **prepend `--repo $REPO_OVERRIDE` before the subcommand in every script invocation** to override auto-detection.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Phase 1: Setup (conditional)

**If state from `start-implementing-issue` is already in the conversation context** (NODE_ID, ITEM_ID, field IDs, and parent info are known), **skip to Phase 2.3.**

Otherwise, follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Fetch Issue (conditional)

**If state from `start-implementing-issue` is already in the conversation context**, **skip to Phase 2.3.**

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
   - `PARENT_REPO` from `.repository.owner.login` + `/` + `.repository.name` (e.g., `owner/repo`). The parent may be in a different repository than the current issue — always use `--repo $PARENT_REPO` for issue-number-based commands on the parent.

## Phase 2.3: Pre-Close Checks

These checks ensure the issue is in a clean state before closing.

1. **If a project is available**, check if the issue has a start date:
   ```bash
   <cli> get-start-date "$NODE_ID"
   ```
   - If the output is **non-empty** and the `.date` field is **not `null`**: start date is already set. Skip to step 2.
   - If the output is **empty** or `.date` is `null`: no start date. Try to auto-detect one:
     ```bash
     <cli> get-status-change-date "$NODE_ID"
     ```
     - If the output is a date (not `null`): suggest that date.
     - If the output is `null`: suggest today's date.
     - **Ask the user:** "Issue has no start date. Set to <suggested date>?"
     - If confirmed:
       - Get the ITEM_ID if not already known:
         ```bash
         <cli> get-project-item "$NODE_ID"
         ```
       - Set the start date:
         ```bash
         <cli> set-date "$ITEM_ID" "$START_FIELD" <date>
         ```

2. Check if the current user is assigned to the issue:
   ```bash
   <cli> issue-get-assignees <number>
   ```
   Check if the current user's login is in the returned JSON array. To determine the current user, the login used during `gh auth status` is available — or simply check if the array is non-empty (if no one is assigned, offer to assign).
   - If the user is **not** in the assignees list: **Ask the user:** "Assign yourself to #<number>?"
   - If confirmed:
     ```bash
     <cli> issue-assign <number>
     ```

## Phase 2.5: Closing Comment

Generate an optional closing comment summarizing what was implemented. This provides context for future sessions reviewing this issue.

1. **Determine available context:**

   - **Check git state:** Run `git rev-parse --abbrev-ref HEAD` to get the current branch. If the branch is not `main` (or the default branch), there may be relevant commits.
   - **If on a non-main branch:** Run `git log main..HEAD --oneline` to get the commit list. Cross-check these commits against the issue title and body to determine relevance. If unsure whether the commits relate to this issue, ask the user.
   - **Conversation context:** If this is a handoff from `start-implementing-issue` (implementation work was done in this session), also use the conversation context — what was discussed, built, and changed.

2. **Generate a summary** using the available context (conversation + git log):

   ```markdown
   ## Implementation Summary

   - <what was done, 3-7 bullets>
   ```

   Each bullet should describe a concrete change. Focus on what changed, not why.

   - If there is **no usable context** (on main branch, no relevant commits, no conversation context): skip the auto-generated summary and go directly to step 3.

3. **Present to the user:**
   - If a summary was generated: "Here's the closing comment that will be posted:" followed by the summary. Ask: **"Post this as a closing comment? (You can also edit it, write your own, or skip.)"**
   - If no summary was generated: **"Would you like to add a closing comment before closing the issue? (You can write one or skip.)"**
   - **If approved (or user provides custom text):** Save as `SUMMARY` for use in Phase 3.
   - **If skipped:** Set `SUMMARY` to empty. The issue will be closed without a comment.

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
        <cli> --repo $PARENT_REPO issue-close <parent_number>
        ```

      - If the user declines, leave the parent as-is.

4. **If a parent issue exists and was not closed in step 3**, check parent assignment:
   ```bash
   <cli> --repo $PARENT_REPO issue-get-assignees <PARENT_NUMBER>
   ```
   - If the current user is **not** in the assignees list: **Ask the user:** "Assign yourself to parent #PARENT_NUMBER (PARENT_TITLE)?"
   - If confirmed:
     ```bash
     <cli> --repo $PARENT_REPO issue-assign <PARENT_NUMBER>
     ```

5. Tell the user the issue is implemented and closed.

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
