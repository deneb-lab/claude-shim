---
name: add-issue
description: Create a GitHub issue from conversation context and add it to the project board with Todo status
---

# GitHub — Add Issue

Create a new GitHub issue from conversation context and add it to the project board.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

## Phase 1: Gather Context

Read the conversation context and any arguments provided. You need:
- **Title:** A clear, concise issue title
- **Body:** Issue description with enough detail to act on
- **Parent (optional):** If the user mentioned a parent issue (e.g., `parent #31`, `make #31 the parent`, `parent https://github.com/owner/repo/issues/31`), extract the parent reference. Support both `#N` (same repo) and full GitHub URLs (cross-repo).

If the context is insufficient, ask the user for clarification.

The default repository is the current git repository (auto-detected by the script). The user can specify a different repo.
The default project is auto-detected from the repo owner's GitHub projects.

## Phase 2: Create Issue

1. Create the issue:
   ```bash
   scripts/github-projects.sh issue-create --title "<title>" --body "<body>"
   ```

   If the user specified a label, add `--label "<label>"`.

   The output is the issue URL. Extract the issue number from the URL path.

2. Get the issue node ID:
   ```bash
   scripts/github-projects.sh issue-view <number> --json id --jq '.id'
   ```

   Save the output as `NODE_ID`.

3. Add to project:
   ```bash
   scripts/github-projects.sh add-to-project "$NODE_ID"
   ```

   Save the output as `ITEM_ID`.

4. Set status to "Todo":
   ```bash
   scripts/github-projects.sh set-status "$ITEM_ID" todo
   ```

## Phase 2.5: Link Parent (conditional)

Skip this phase if no parent was specified in Phase 1.

1. Resolve the parent issue's node ID:
   - Same-repo (`#N`):
     ```bash
     scripts/github-projects.sh issue-view <N> --json id --jq '.id'
     ```
   - Cross-repo (full URL):
     ```bash
     scripts/github-projects.sh issue-view <url> --json id --jq '.id'
     ```

   Save the output as `PARENT_NODE_ID`.

2. Link the new issue as a sub-issue of the parent:
   ```bash
   scripts/github-projects.sh set-parent "$NODE_ID" "$PARENT_NODE_ID"
   ```

## Phase 3: Report

Tell the user the issue was created and provide the URL.

If a parent was linked in Phase 2.5, also report: "Linked as sub-issue of #N (title)."

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
