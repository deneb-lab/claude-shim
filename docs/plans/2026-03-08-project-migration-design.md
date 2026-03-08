# GitHub Project Migration Design

## Context

Repositories were transferred from personal account (elahti) to organization (deneb-lab). Issues moved with the repos, but the GitHub Project board remained under the personal account at `https://github.com/users/elahti/projects/1`.

A new org project has been created at `https://github.com/orgs/deneb-lab/projects/1` with all required fields (Status, Start date, End date) and issue types (Task, Bug) configured. The `.claude-shim.json` in all repos has been updated with the new project's field IDs.

## Goal

Migrate all issues from 7 deneb-lab repositories to the new org project, preserving metadata from the old project where it exists, so the old personal project can be retired.

## Repositories

- deneb-lab/deneb (54 issues)
- deneb-lab/claude-shim (2 issues)
- deneb-lab/k0s-dev-environment (17 issues)
- deneb-lab/eu-ai-act (9 issues)
- deneb-lab/deneb-marketplace (59 issues)
- deneb-lab/stellaris-stats (1 issue)
- deneb-lab/devcontainer (1 issue)

**Total: 143 issues**

## Old Project State

- 30 items tracked (25 from deneb, 5 from deneb-marketplace)
- 25 items have start and/or end dates
- Statuses: 21 Done, 1 In Progress, 3 Todo (deneb); 5 Done (deneb-marketplace)
- No issue types on old project

## Migration Rules

### Status
- **30 items on old project:** Preserve existing status (Done/In Progress/Todo)
- **~113 items not on old project:** Closed issues -> Done, Open issues -> Todo

### Dates
- **25 items with dates on old project:** Migrate start date and end date values
- **All other items:** No dates set

### Issue Types
- **Default:** Task (`IT_kwDOD-Fm1s4B44fF`)
- **Bug:** Use for issues whose title/body clearly describes a bug (e.g. "Fix broken...", "error", crash reports) (`IT_kwDOD-Fm1s4B44fG`)

## Field IDs (new project)

- Project: `deneb-lab/projects/1`
- Status field: `PVTSSF_lADOD-Fm1s4BRGlTzg_B3r0`
  - Todo: `f75ad846`
  - In Progress: `47fc9ee4`
  - Done: `98236657`
- Start date: `PVTF_lADOD-Fm1s4BRGlTzg_CVrI`
- End date: `PVTF_lADOD-Fm1s4BRGlTzg_CVsc`

## Approach

1. Fetch all items from old project with their status, start date, and end date
2. For each of the 7 repos, list all issues (open + closed)
3. Add each issue to the new project via `gh project item-add`
4. Set fields on each item:
   - Status (preserved or derived)
   - Start/end dates (if from old project)
   - Issue type (Task or Bug based on judgement)
5. Verify migration completeness

## Risk

Low. Adding items to a project is non-destructive and idempotent. The 1 item already on the new project won't be duplicated.
