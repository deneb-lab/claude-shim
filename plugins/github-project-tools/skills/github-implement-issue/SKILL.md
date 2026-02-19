---
name: github:implement-issue
description: Implement a GitHub issue with full project lifecycle management (dates, statuses, closing)
---

# GitHub — Implement Issue

Implement a GitHub issue with full project lifecycle management: start/end dates, status transitions, and closing. Automatically detects and manages parent issue lifecycle when the issue is a sub-issue.

The user provides an issue number or URL as an argument.

## Phase 1: Fetch Issue Context

1. Get the issue details:
   ```bash
   scripts/github-projects.sh issue-view <number> --json id,number,title,body,state
   ```

2. Verify the issue is open. If closed, tell the user and stop.

3. Save the node ID (from the `id` field) as `NODE_ID`.

4. **Check for a parent issue:**
   ```bash
   scripts/github-projects.sh get-parent "$NODE_ID"
   ```

   If the output is not `null`:
   - Save `PARENT_ID` (from `.id`), `PARENT_NUMBER` (from `.number`)
   - Get the parent issue body to check for an Action Plan table:
     ```bash
     scripts/github-projects.sh issue-view <parent_number> --json body --jq '.body'
     ```
   - Save `HAS_TABLE=true` if the body contains a markdown table with issue references, otherwise `HAS_TABLE=false`

## Phase 2: Set Start State

1. **Look up date field IDs:**
   ```bash
   scripts/github-projects.sh get-project-fields
   ```

   Save `START_FIELD` from `.start` and `END_FIELD` from `.end`.

2. **Get project item ID:**
   ```bash
   scripts/github-projects.sh get-project-item "$NODE_ID"
   ```

   If the output is empty (issue not in project), add it first:
   ```bash
   scripts/github-projects.sh add-to-project "$NODE_ID"
   ```

   Save the output as `ITEM_ID`.

3. **Set start date** to today:
   ```bash
   scripts/github-projects.sh set-date "$ITEM_ID" "$START_FIELD" "$(date +%Y-%m-%d)"
   ```

4. **Set status** to "In Progress":
   ```bash
   scripts/github-projects.sh set-status "$ITEM_ID" in-progress
   ```

5. **If parent exists:**

   a. **Update Action Plan table** (only if `HAS_TABLE=true`):
      ```bash
      scripts/github-projects.sh table-set-status <parent_number> <issue_number> "In Progress"
      ```

   b. **Check parent start date:**
      ```bash
      scripts/github-projects.sh get-start-date "$PARENT_ID"
      ```

      The output is JSON with `item_id` and `date` keys. Save `PARENT_ITEM` from `.item_id` and `PARENT_DATE` from `.date`.

      If `PARENT_DATE` is `"null"` (parent has no start date set), set the start date:
      ```bash
      scripts/github-projects.sh set-date "$PARENT_ITEM" "$START_FIELD" "$(date +%Y-%m-%d)"
      ```

      And set the parent status:
      ```bash
      scripts/github-projects.sh set-status "$PARENT_ITEM" in-progress
      ```

## Phase 3: Implement

Invoke the `superpowers:brainstorming` skill with the issue context:

```
Skill: superpowers:brainstorming

Context from GitHub issue #<number>:

Title: <issue title>

<issue body>

IMPORTANT: The design plan MUST include verification steps that confirm the implementation works correctly. These verification steps will be executed before the issue can be marked as done.

If this issue involves infrastructure or server changes (Ansible roles, Helm charts, Kubernetes manifests, etc.), the plan MUST include:
1. Prompt the user to apply the Ansible playbook with the appropriate --tags
2. Wait for user confirmation that the playbook has been applied
3. Verify the change took effect via `ssh esko@phoebe.fi claude-remote ...` commands
```

This triggers the full brainstorm → design → writing-plans → implementation flow. Follow it through to completion.

If at any point during implementation you determine the issue **cannot be implemented** (e.g., waiting for an upstream release, blocked by external factors), skip to **Phase 5: Can't Implement**.

## Phase 4: Set End State

Only proceed here after implementation is complete AND verification steps have passed.

1. **Set end date** to today:
   ```bash
   scripts/github-projects.sh set-date "$ITEM_ID" "$END_FIELD" "$(date +%Y-%m-%d)"
   ```

2. **Set status** to "Done":
   ```bash
   scripts/github-projects.sh set-status "$ITEM_ID" done
   ```

3. **Close the issue:**
   ```bash
   scripts/github-projects.sh issue-close <number>
   ```

4. **If parent exists:**

   a. **Update Action Plan table** (only if `HAS_TABLE=true`):
      ```bash
      scripts/github-projects.sh table-set-status <parent_number> <issue_number> "✅ Done"
      ```

   b. **Check if this was the last sub-issue:**

      Get the parent project item:
      ```bash
      scripts/github-projects.sh get-project-item "$PARENT_ID"
      ```

      Save the output as `PARENT_ITEM`.

      Count remaining open sub-issues:
      ```bash
      scripts/github-projects.sh count-open-sub-issues "$PARENT_ID"
      ```

      Save the output as `OPEN_COUNT`.

      If `OPEN_COUNT` is 0:
      ```bash
      scripts/github-projects.sh set-date "$PARENT_ITEM" "$END_FIELD" "$(date +%Y-%m-%d)"
      scripts/github-projects.sh issue-close <parent_number>
      scripts/github-projects.sh set-status "$PARENT_ITEM" done
      ```

      Tell the user: "All sub-issues resolved. Parent issue #<parent_number> closed."

5. Tell the user the issue is implemented and closed.

## Phase 5: Can't Implement

Use this phase instead of Phase 4 when the issue cannot be implemented (e.g., waiting for upstream release, blocked by external factors).

1. **Reset status** to "Todo":
   ```bash
   scripts/github-projects.sh set-status "$ITEM_ID" todo
   ```

2. **If parent exists and `HAS_TABLE=true`:**
   ```bash
   scripts/github-projects.sh table-set-status <parent_number> <issue_number> "Open"
   ```

3. **Leave the issue open.** Do not set an end date or close the issue.

4. **Tell the user** why the issue can't be implemented and what needs to happen before it can be revisited.

## Important Notes

- **All bash commands** must start with the script being invoked — never wrap in variable assignments like `VAR=$(scripts/...)`. Run the command, then use the output.
- **JSON processing:** Extract values from command output in-context. Do not use separate `echo | jq` bash commands.
- **All GitHub operations** go through `scripts/github-projects.sh` — never call `gh` directly.
- **Date field IDs:** Look up at runtime (Phase 2 step 1) — they may change if the project is recreated.
- **Do not mark done** until verification steps from the brainstorming design have passed.
- **Allowed Action Plan table statuses:** `Open`, `In Progress`, `✅ Done` — no other values.
