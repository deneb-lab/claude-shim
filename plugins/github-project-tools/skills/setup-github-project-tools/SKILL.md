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

Each stage can map to **one or more** status options. When multiple options map to the same stage, one must be marked as the **default** — the value used when the skill sets status for that stage.

Using the status field's `.options` array from Step 4, auto-match option names to these stages:

| Stage | Try matching (case-insensitive) |
|-------|-------------------------------|
| New issues | "Todo", "To Do", "To do", "Backlog", "New" |
| Started work | "In Progress", "In progress", "Working", "Active", "Doing" |
| Finished work | "Done", "Complete", "Completed", "Shipped", "Closed" |

For each stage:
1. Auto-match candidates from the options list using the name patterns above.
2. Present **all** status options to the user with AskUserQuestion using `multiSelect: true`. Pre-select any auto-matched options by listing them first and marking them as "(Recommended)" in the label.
3. The user selects which options map to this stage (one or more).
4. If multiple options were selected, ask the user which one should be the **default** (the status value used when the skill sets status for this stage).
5. If only one option was selected, it is automatically the default.

Present the proposed mapping for confirmation:
```
Status mappings:
  New issues    → "Todo" (default)
  Started work  → "In Progress" (default)
  Finished work → "Done" (default), "Arkisto"
```

Ask: "Does this look right?"

## Step 5.5: Detect Issue Types

Query available issue types for the repository:
```bash
<cli> list-issue-types
```

- **If the command returns an empty array `[]`:** Tell the user: "No issue types available for this repository. Skipping issue type configuration." Proceed to Step 6.

- **If issue types are returned:** Present them to the user with AskUserQuestion using `multiSelect: true`: "Which issue types should be available in the config?" List all returned types as options.

  - If the user selects **one or more types**, ask which one should be the **default** (single-select AskUserQuestion). The default type is used automatically when creating issues via the `add-issue` skill.
  - If the user selects **no types** (declines all), skip issue type configuration.

Save the selections as `ISSUE_TYPES` for Step 6. Each entry has `name`, `id`, and `default` (true for exactly one).

## Step 6: Write Config

Build the configuration object. **Always write status mappings as lists**, even when a stage has only one option:

```json
{
  "github-project-tools": {
    "repo": "<REPO>",
    "project": "<PROJECT_URL>",
    "fields": {
      "start-date": { "id": "<START_FIELD_ID>", "type": "DATE" },
      "end-date": { "id": "<END_FIELD_ID>", "type": "DATE" },
      "status": {
        "id": "<STATUS_FIELD_ID>",
        "todo": [{ "name": "<name>", "option-id": "<id>", "default": true }],
        "in-progress": [{ "name": "<name>", "option-id": "<id>", "default": true }],
        "done": [
          { "name": "<name>", "option-id": "<id>", "default": true },
          { "name": "<name2>", "option-id": "<id2>" }
        ]
      },
      "issue-types": [
        { "name": "<name>", "id": "<id>", "default": true },
        { "name": "<name2>", "id": "<id2>" }
      ]
    }
  }
}
```

Non-default items in the list omit the `"default"` key (it defaults to `false`).

**`issue-types` is optional.** Omit the key entirely if no issue types were selected in Step 5.5.

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
