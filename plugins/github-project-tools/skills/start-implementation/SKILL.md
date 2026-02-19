---
name: start-implementation
description: Start implementing a GitHub issue - assigns, sets dates/status, creates draft PR, and presents issue context
allowed-tools: Bash(github-projects.sh:*), Bash(find:*), Bash(date:*), Bash(git:*), Bash(basename:*)
---

# GitHub Projects — Start Implementation

Start working on a GitHub issue: assign yourself, update project board dates and status, optionally create a draft PR, then present the issue context so you can begin implementation.

## Phase 0: Preflight

1. Find the bundled script at `~/.claude/plugins/**/github-project-tools/scripts/github-projects.sh`
2. Run preflight checks:
   ```bash
   scripts/github-projects.sh preflight
   ```
3. If preflight fails, stop and show the error message to the user. Do not proceed.

## Phase 1: Setup

The script auto-detects the current repository from the git remote, so no manual repo configuration is needed.

1. Get project fields (date field IDs):
   ```bash
   scripts/github-projects.sh get-project-fields
   ```
   This returns JSON with `start` and `end` field IDs. Save these as `START_FIELD` and `END_FIELD`.

   If this command fails because no project is found, note that **no project is available**. Skip all project operations (get-project-item, add-to-project, set-date, set-status) in later phases. Continue with issue-only operations.

2. The `set-status` subcommand accepts the literal arguments `todo`, `in-progress`, and `done` directly — no manual mapping of project-specific status names is needed.

## Phase 2: Fetch Issue

1. Parse the argument. The user provides either:
   - A plain issue number like `42`
   - A full GitHub URL like `https://github.com/owner/repo/issues/42`

   Extract the issue number from whichever format is provided.

2. Fetch the issue details:
   ```bash
   scripts/github-projects.sh issue-view <number> --json id,number,title,body,state
   ```
   Save the JSON output. Extract the issue `id` as `NODE_ID`, `title`, `body`, and `state`.

3. Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is closed and stop.

4. Check for a parent issue:
   ```bash
   scripts/github-projects.sh get-parent "$NODE_ID"
   ```
   If the result is not `null`, save:
   - `PARENT_ID` from `.id`
   - `PARENT_NUMBER` from `.number`
   - `PARENT_TITLE` from `.title`

## Phase 3: Set Start State

Before making any changes, note the current status of the issue (and parent if applicable) so it can be restored if needed in Phase 5.

1. Assign the issue to yourself:
   ```bash
   scripts/github-projects.sh issue-assign <number>
   ```

2. **If a project is available:**

   a. Check if the issue is already on the project board:
      ```bash
      scripts/github-projects.sh get-project-item "$NODE_ID"
      ```
      - If the output is **non-empty**, that value is `ITEM_ID`.
      - If the output is **empty**, add the issue to the project:
        ```bash
        scripts/github-projects.sh add-to-project "$NODE_ID"
        ```
        The output of `add-to-project` is `ITEM_ID`.

   b. Set the start date to today:
      ```bash
      scripts/github-projects.sh set-date "$ITEM_ID" "$START_FIELD" "$(date +%Y-%m-%d)"
      ```

   c. Set status to in-progress:
      ```bash
      scripts/github-projects.sh set-status "$ITEM_ID" in-progress
      ```

3. **If a parent issue exists AND a project is available:**

   a. Get the parent's start date:
      ```bash
      scripts/github-projects.sh get-start-date "$PARENT_ID"
      ```
      Save `PARENT_ITEM` from `.item_id` and `PARENT_DATE` from `.date`.

   b. If `PARENT_DATE` is `"null"` (the parent has no start date set):
      - **Ask the user:** "Parent #PARENT_NUMBER (PARENT_TITLE) has no start date. Set start date to today and status to in-progress?"
      - **Only proceed if the user confirms.**
      - If confirmed:
        ```bash
        scripts/github-projects.sh set-date "$PARENT_ITEM" "$START_FIELD" "$(date +%Y-%m-%d)"
        ```
        ```bash
        scripts/github-projects.sh set-status "$PARENT_ITEM" in-progress
        ```

4. Ask the user: "Create a draft PR linked to this issue?"
   - If yes:
     ```bash
     scripts/github-projects.sh pr-create-draft <number>
     ```
   - If no, skip this step.

5. **Ask the user** how they want to set up their workspace. Suggest a branch name based on the issue: `feat/<issue-number>-<slug>` where the slug is the issue title lowercased, spaces replaced by hyphens, special characters removed.

   Offer three options:

   a. **Feature branch** (recommended) — create and switch to the branch:
      ```bash
      git checkout -b <branch-name>
      ```

   b. **Git worktree** — ask which directory:
      - `../<repoName>__worktrees/<branch-name>` (recommended — sibling directory, use `basename` of `git rev-parse --show-toplevel` for repoName)
      - `.worktrees/<branch-name>` (project-local, hidden)

      Then create the worktree:
      ```bash
      git worktree add <path> -b <branch-name>
      ```

   c. **Stay on current branch** — skip workspace setup entirely.

## Phase 4: Implement

Present the issue context to the user:

```
Issue #<number>: <title>

<body>
```

Then follow whatever additional instructions the user provided in `$ARGUMENTS` (everything after the issue number/URL). For example, the user may have written:

- `<number> use superpowers:brainstorm to implement` → invoke that skill
- `<number> just set up the issue, I'll implement manually` → stop after Phase 3 (do not present the issue or proceed further)
- Any other instructions → follow them

If no additional instructions were provided, proceed with implementation based on the issue description.

## Phase 5: Handoff

When the user indicates they are done (or you have completed the implementation), ask:

**"Implementation complete. Run end-implementation to close the issue?"**

- **If yes:** Invoke `github-project-tools:end-implementation` via the Skill tool. State (NODE_ID, ITEM_ID, field IDs, parent info) will carry through in the conversation context.

- **If no:** Tell the user they can run `/github-project-tools:end-implementation` later to close the issue and update the project board.

- **If the implementation cannot be completed:** Present the user with two options:
  - **Option A: Do nothing** — Leave the issue assigned, dates set, and status as in-progress. The user can continue later.
  - **Option B: Reset** — Restore the issue and parent (if touched) to their original state before this skill ran:
    - Reset the issue status:
      ```bash
      scripts/github-projects.sh set-status "$ITEM_ID" todo
      ```
    - Note: there is no `clear-date` subcommand, so the start date cannot be removed. Resetting the status back to `todo` is the best approximation.
    - If the parent was touched, reset its status to whatever it was before Phase 3:
      ```bash
      scripts/github-projects.sh set-status "$PARENT_ITEM" <original-status>
      ```

## Important Notes

- **All bash commands** must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `scripts/github-projects.sh` — never call `gh` directly.
- **Date field IDs** are looked up at runtime via `get-project-fields` — they may change if the project is recreated.
- **Project is optional.** If no project is detected in Phase 1, skip all project operations (get-project-item, add-to-project, set-date, set-status) but still perform issue operations (assign, view, parent check).
