---
name: add-issue
description: Create a GitHub issue from conversation context and add it to the project board with Todo status
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh repo-detect), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-create *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-parent *)
---

# GitHub — Add Issue

Create a new GitHub issue from conversation context and add it to the project board.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Phase 1: Setup

Follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Gather Context

Read the conversation context and any arguments provided. You need:
- **Title:** A clear, concise issue title
- **Body:** Issue description with enough detail to act on
- **Parent (optional):** If the user mentioned a parent issue (e.g., `parent #31`, `make #31 the parent`, `parent https://github.com/owner/repo/issues/31`), extract the parent reference. Support both `#N` (same repo) and full GitHub URLs (cross-repo).
- **Issue type (optional):** If the user specified an issue type (e.g., "Epic", "Bug", "Task"). If not specified and config has `issue-types` configured (non-null in `read-config` output), use the default type from config (the entry with `"default": true`).

If the context is insufficient, ask the user for clarification.

The default repository is the current git repository (auto-detected by the script). The user can specify a different repo.
The default project is auto-detected from the repo owner's GitHub projects.

## Phase 3: Create Issue

1. Create the issue:

   **If issue types are configured** (the `read-config` output contains a non-null `issue-types` field):
   ```bash
   <cli> issue-create --title "<title>" --body "<body>" --issue-type "<type-name>"
   ```
   Use the user-specified type, or the default type from config (the entry with `"default": true`).

   **If issue types are not configured:**
   ```bash
   <cli> issue-create --title "<title>" --body "<body>"
   ```

   The output is the issue URL. Extract the issue number from the URL path.

2. Get the issue node ID:
   ```bash
   <cli> issue-view <number> --json id --jq '.id'
   ```

   Save the output as `NODE_ID`.

3. **If a project is available** (config was loaded successfully in Phase 1):

   a. Add to project:
      ```bash
      <cli> add-to-project "$NODE_ID"
      ```

      Save the output as `ITEM_ID`.

   b. Set status to "Todo":
      ```bash
      <cli> set-status "$ITEM_ID" todo
      ```

## Phase 3.5: Link Parent (conditional)

Skip this phase if no parent was specified in Phase 2.

1. Resolve the parent issue's node ID:
   - Same-repo (`#N`):
     ```bash
     <cli> issue-view <N> --json id --jq '.id'
     ```
   - Cross-repo (full URL):
     ```bash
     <cli> issue-view <url> --json id --jq '.id'
     ```

   Save the output as `PARENT_NODE_ID`.

2. Link the new issue as a sub-issue of the parent:
   ```bash
   <cli> set-parent "$NODE_ID" "$PARENT_NODE_ID"
   ```

## Phase 4: Report

Tell the user the issue was created and provide the URL.

If a parent was linked in Phase 3.5, also report: "Linked as sub-issue of #N (title)."

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
