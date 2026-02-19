---
name: github:add-issue
description: Create a GitHub issue from conversation context and add it to the project board with Todo status
---

# GitHub — Add Issue

Create a new GitHub issue from conversation context and add it to the Deneb project board.

## Phase 1: Gather Context

Read the conversation context and any arguments provided. You need:
- **Title:** A clear, concise issue title
- **Body:** Issue description with enough detail to act on

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

## Phase 3: Report

Tell the user the issue was created and provide the URL.

## Important Notes

- **All bash commands** must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `scripts/github-projects.sh` — never call `gh` directly.
