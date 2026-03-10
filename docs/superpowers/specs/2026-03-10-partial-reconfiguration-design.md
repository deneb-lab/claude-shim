# Partial Reconfiguration for setup-github-project-tools

**Issue:** [#88](https://github.com/deneb-lab/deneb-marketplace/issues/88)
**Date:** 2026-03-10

## Problem

When a user invokes `setup-github-project-tools` with an existing config, the only options are "Keep current config" or "Reconfigure" (full). Users who need to change a single section (e.g., status mappings after adding a new column) must re-answer every question.

## Design

Modify Step 1 of the setup SKILL.md to present a multi-select menu when existing config is found. Only the selected sections (plus cascading dependents) run their detection steps. Unselected sections retain current values.

This is a deliberate removal of the existing "Keep current config" option in Step 1. Users who invoke the setup skill want to change something.

### Multi-select menu

When `read-config` succeeds, show a summary of current config and a multi-select:

```
Current configuration:
  Repo:            deneb-lab/deneb-marketplace
  Project:         https://github.com/orgs/deneb-lab/projects/1
  Status mappings: Todo (default) | In Progress (default) | Done (default), Arkisto
  Issue types:     Task, Bug, Feature (default)

What would you like to reconfigure?
  [ ] Repository (also reconfigures: project, fields, status mappings)
  [ ] Project (also reconfigures: fields, status mappings)
  [ ] Status mappings
  [ ] Issue types
```

When a status stage has multiple options, show all of them with the default marked (e.g., `Done (default), Arkisto`).

When multiple options are selected, the union of all cascade chains determines which steps execute. For example, selecting both "Repository" and "Issue types" runs Steps 2, 3, 4, 5, and 5.5.

### Cascade rules

| Option | Runs steps | Cascade |
|--------|-----------|---------|
| Repository | Steps 2, 3, 4, 5 | Project + fields + status mappings (new owner may have different projects) |
| Project | Steps 3, 4, 5 | Fields + status mappings always included |
| Status mappings | Step 5 | None (uses existing status field ID from config) |
| Issue types | Step 5.5 | None |

When the user selects an option that cascades, the dependent steps run automatically without asking the user to confirm the cascade.

Date fields (start-date, end-date) are not a standalone option. They are project-specific and always reconfigured together with the project. Users who add a new date field to an existing project select "Project" to re-detect all project fields.

### Status mappings without project re-detection

When only "Status mappings" is selected (Step 5 runs but Step 4 does not), the status field's options array is not available from Step 4. To obtain it, use the existing `STATUS_FIELD_ID` from the current config and fetch the project's fields:

```bash
<cli> project-field-list --owner "$OWNER" "$PROJECT_NUMBER"
```

Extract `OWNER` and `PROJECT_NUMBER` from the existing config's `project` URL (e.g., `https://github.com/orgs/deneb-lab/projects/1` gives owner `deneb-lab` and number `1`). Find the status field by matching `STATUS_FIELD_ID` against the returned fields, then use its `.options` array for Step 5.

### Step 6 (Write Config) merge rules

Instead of building a fresh config object, start from the existing config and replace only the sections that were reconfigured. The merge granularity per option:

| Option selected | Config keys replaced |
|----------------|---------------------|
| Repository | `repo` |
| Project | `project`, `fields.start-date`, `fields.end-date`, `fields.status` (entire object including `id` and mappings) |
| Status mappings | `fields.status.todo`, `fields.status.in-progress`, `fields.status.done` (preserves `fields.status.id`) |
| Issue types | `fields.issue-types` |

Unselected sections carry through unchanged from the existing config.

### No-config path

When `read-config` fails (no existing config), skip the multi-select and run all steps. Same behavior as today.

## Scope

### Changed

- `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md` -- rewrite Step 1, adjust Step 6 merge logic

### Unchanged

- CLI script (`github-project-tools.sh`)
- Python code (`cli.py`, `config.py`)
- Other skills (add-issue, start-implementing-issue, end-implementing-issue, mass-update-issues)
- Shared prompt files (preflight.md, conventions.md)
- Config schema
