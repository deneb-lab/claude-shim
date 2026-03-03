---
name: start-implementation
description: Start implementing a GitHub issue - assigns, sets dates/status, and presents issue context
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-parent *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *), Bash(git rev-parse *), Bash(git checkout *), Bash(git worktree *)
---

# GitHub Projects — Start Implementation

Start working on a GitHub issue: assign yourself, update project board dates and status, then present the issue context so you can begin implementation.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Phase 1: Setup

Follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Fetch Issue

1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).

2. Fetch the issue details:
   ```bash
   <cli> issue-view-full <number>
   ```
   Save the JSON output. Extract the issue `id` as `NODE_ID`, `title`, `body`, and `state`.

3. Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is closed and stop.

4. Check for a parent issue:
   ```bash
   <cli> get-parent "$NODE_ID"
   ```
   If the result is not `null`, save:
   - `PARENT_ID` from `.id`
   - `PARENT_NUMBER` from `.number`
   - `PARENT_TITLE` from `.title`

## Phase 3: Set Start State

Before making any changes, note the current status of the issue (and parent if applicable) so it can be restored if needed in Phase 5.

1. Check if already assigned to the issue:
   ```bash
   <cli> issue-get-assignees <number>
   ```
   Check if the current user's login is in the returned JSON array. If already assigned, skip to step 2. Otherwise, assign:
   ```bash
   <cli> issue-assign <number>
   ```

2. **If a project is available:**

   a. Check if the issue is on the project board and whether a start date is already set:
      ```bash
      <cli> get-start-date "$NODE_ID"
      ```
      - If the output is **non-empty**: extract `ITEM_ID` from `.item_id` and `ISSUE_DATE` from `.date`. Proceed to (b).
      - If the output is **empty**: the issue is not on the project board. Add it:
        ```bash
        <cli> add-to-project "$NODE_ID"
        ```
        The output is `ITEM_ID`. `ISSUE_DATE` is implicitly `"null"`. Proceed to (b).

   b. If `ISSUE_DATE` is `"null"` (no start date set), set it to today:
      ```bash
      <cli> set-date "$ITEM_ID" "$START_FIELD"
      ```

   c. Set status to in-progress:
      ```bash
      <cli> set-status "$ITEM_ID" in-progress
      ```

3. **If a parent issue exists AND a project is available:**

   a. Check if the parent is on the project board:
      ```bash
      <cli> get-start-date "$PARENT_ID"
      ```
      - If the output is **non-empty**: extract `PARENT_ITEM` from `.item_id` and `PARENT_DATE` from `.date`. Proceed to (b).
      - If the output is **empty**: the parent is not on the project board. **Ask the user:**
        "Parent #PARENT_NUMBER (PARENT_TITLE) is not on the project board. Add it? (Start date and status can only be set for issues on the board.)"
        - If the user confirms:
          ```bash
          <cli> add-to-project "$PARENT_ID"
          ```
          The output is `PARENT_ITEM`. `PARENT_DATE` is implicitly `"null"`. Proceed to (b).
        - If the user declines: **skip all remaining parent project operations** (date, status). Jump to step 4.

   b. If `PARENT_DATE` is `"null"` (the parent has no start date set), set it to today:
      ```bash
      <cli> set-date "$PARENT_ITEM" "$START_FIELD"
      ```

   c. Set parent status to in-progress (idempotent — safe even if already in-progress):
      ```bash
      <cli> set-status "$PARENT_ITEM" in-progress
      ```

4. **If a parent issue exists** (regardless of project board status), check parent assignment:
   ```bash
   <cli> issue-get-assignees <PARENT_NUMBER>
   ```
   - If the current user is already in the assignees list, skip.
   - If the current user is **not** in the assignees list, **ask the user:** "Assign yourself to parent #PARENT_NUMBER (PARENT_TITLE)?"
   - **Only proceed if the user confirms.**
   - If confirmed:
     ```bash
     <cli> issue-assign <PARENT_NUMBER>
     ```

5. **Set up the workspace.**

   First, check if the user is already on a non-main worktree:
   ```bash
   git rev-parse --absolute-git-dir
   ```
   If the output contains `.git/worktrees/`, this is a secondary worktree. Then check the current branch:
   ```bash
   git rev-parse --abbrev-ref HEAD
   ```
   If the branch is not `main` (or whatever the default branch is), **skip the rest of this step** and tell the user: "Already on worktree branch `<branch>` — skipping workspace setup."

   Otherwise, ask the user how they want to set up their workspace. Suggest a branch name based on the issue: `feat/<issue-number>-<slug>` where the slug is the issue title lowercased, spaces replaced by hyphens, special characters removed.

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
      <cli> set-status "$ITEM_ID" todo
      ```
    - Note: there is no `clear-date` subcommand, so the start date cannot be removed. Resetting the status back to `todo` is the best approximation.
    - If the parent was touched, reset its status to whatever it was before Phase 3:
      ```bash
      <cli> set-status "$PARENT_ITEM" <original-status>
      ```

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
