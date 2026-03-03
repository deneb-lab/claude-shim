---
name: setup-github-project-tools
description: Set up or modify github-project-tools configuration in .claude-shim.json for the current repository
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh *)
---

# GitHub Projects — Setup

Configure the github-project-tools plugin for this repository. Detects your GitHub Project, field IDs, and status mappings, then writes the configuration to `.claude-shim.json`.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Step 1: Check for Existing Config

Run:
```bash
<cli> read-config
```

- **If the command succeeds** (exit code 0, outputs JSON): Show the user a summary of the current configuration (project URL, field names, status mappings). Ask using AskUserQuestion:
  1. **Keep current config** — stop, no changes needed.
  2. **Reconfigure** — proceed to Step 2, overwriting the existing config.

- **If the command fails** (exit code 1): Proceed directly to Step 2.

## Step 2: Detect Repository

Auto-detect the repository:
```bash
<cli> repo-detect
```

Save the output as `REPO` (e.g., `owner/repo`). Extract `OWNER` as the part before `/`.

Use AskUserQuestion to confirm with the user: "Detected repository: `REPO`. Issues will be created and managed in this repository."
- **Yes, use this repository** — proceed to Step 3.
- **No, let me specify** — ask the user for the correct `owner/repo` value, save it as `REPO`, re-extract `OWNER`, and proceed to Step 3.

## Step 3: Detect Project

List the owner's projects:
```bash
<cli> project-list --owner "$OWNER"
```

Parse the JSON output. The `.projects` array contains objects with `number`, `title`, `id`, and `url`.

- **If no projects found:** Tell the user "No GitHub Projects found for owner `OWNER`. Create a project first, then re-run this setup." Stop.

- **If exactly one project:** Use AskUserQuestion to confirm: "Found one project: `title` (`url`)."
  - **Yes, use this project** — proceed.
  - **No** — tell the user "No other projects found for owner `OWNER`. Create another project first, then re-run this setup." Stop.

- **If multiple projects:** Try to auto-detect which project is used by this repo:
  ```bash
  <cli> issue-list --limit 5 --json number,projectItems
  ```
  Check if any returned issues have `projectItems` linking to one of the listed projects. If a match is found, recommend that project.

  Present the list of projects to the user with AskUserQuestion, highlighting the recommendation if any. User picks one.

Save `PROJECT_URL`, `PROJECT_NUMBER`, and `PROJECT_ID` from the selected project.

## Step 4: Detect Field IDs

Get the project's fields:
```bash
<cli> project-field-list --owner "$OWNER" "$PROJECT_NUMBER"
```

Parse the JSON output. The `.fields` array contains objects with `name`, `id`, and `type`.

**Date fields:** Look for fields with names matching (case-insensitive):
- Start date: "Start date", "Start Date", "Start"
- End date: "End date", "End Date", "End", "Due date", "Due Date"

If auto-detection finds matches, save `START_FIELD_ID` and `END_FIELD_ID`. Confirm with the user.

If auto-detection fails for either field, present the full list of date-type fields and ask the user to pick.

**Status field:** Look for a field named "Status" (case-insensitive). Save `STATUS_FIELD_ID` and the field's `.options` array.

If no "Status" field is found, present all single-select fields and ask the user to pick.

## Step 5: Detect Status Mappings

The plugin automatically updates issue status as you work — it needs to know which of your project's status options correspond to three workflow stages:

- **New issues** — set when creating an issue or resetting one that was started but not completed
- **Started work** — set when you begin implementing an issue
- **Finished work** — set when you close an issue after implementation is complete

Using the status field's `.options` array from Step 4, auto-match option names to these stages:

| Stage | Try matching (case-insensitive) |
|-------|-------------------------------|
| New issues | "Todo", "To Do", "To do", "Backlog", "New" |
| Started work | "In Progress", "In progress", "Working", "Active", "Doing" |
| Finished work | "Done", "Complete", "Completed", "Shipped", "Closed" |

For each stage:
- If exactly one option matches, auto-assign it.
- If multiple options match, ask the user to pick.
- If no options match, present the full list and ask the user to assign.

Present the proposed mapping for confirmation:
```
Status mappings:
  New issues    → "Todo"
  Started work  → "In Progress"
  Finished work → "Done"
```

Ask: "Does this look right?"

## Step 6: Write Config

Build the configuration object:
```json
{
  "github-project-tools": {
    "project": "<PROJECT_URL>",
    "fields": {
      "start-date": "<START_FIELD_ID>",
      "end-date": "<END_FIELD_ID>",
      "status": {
        "id": "<STATUS_FIELD_ID>",
        "todo": { "name": "<name>", "option-id": "<id>" },
        "in-progress": { "name": "<name>", "option-id": "<id>" },
        "done": { "name": "<name>", "option-id": "<id>" }
      }
    }
  }
}
```

Present the final config JSON to the user.

<HARD-GATE>
Do NOT write `.claude-shim.json` until the user has explicitly approved. Use AskUserQuestion:
- **Approve and write** — proceed to write the file.
- **Make changes** — ask what to change, update the config, and present again.
</HARD-GATE>

**Write to `.claude-shim.json`:**
- If the file exists: read it, add or replace the `github-project-tools` key, preserve all other keys (like `quality-checks`), write back.
- If the file doesn't exist: create it with just the `github-project-tools` key.

Use the Write tool to save the file.

## Step 7: Confirm

Tell the user:

> Configuration saved to `.claude-shim.json`. The github-project-tools skills will now use this configuration.
>
> Re-run this skill anytime to review or update the configuration.

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).
