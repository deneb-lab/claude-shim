# Design: Support GitHub Issue Types in issue-create

**Issue:** [elahti/deneb-marketplace#82](https://github.com/elahti/deneb-marketplace/issues/82)
**Date:** 2026-03-06

## Problem

The `issue-create` command and `add-issue` skill have no support for GitHub issue types (Epic, Task, Bug, Feature). Issue types are set via the GraphQL API using `issueTypeId` on `createIssue`/`updateIssue` mutations. Users must manually call GraphQL to set types after creation.

## Approach

Config-driven, two-step create-then-update. Issue types are stored in `.claude-shim.json` alongside existing field config. The CLI resolves type names from config, creates the issue with `gh issue create`, then sets the type via `updateIssue` GraphQL mutation.

## Config Model

Add `IssueType` model and optional `issue-types` field to `ProjectFields`:

```python
class IssueType(BaseModel):
    name: str
    id: str
    default: bool = False

class ProjectFields(BaseModel):
    start_date: str = Field(alias="start-date")
    end_date: str = Field(alias="end-date")
    status: StatusField
    issue_types: list[IssueType] | None = Field(None, alias="issue-types")
```

Add validator: when `issue-types` is a non-empty list, exactly one entry must have `default: true`.

JSON shape:

```json
"fields": {
  "start-date": "PVTF_...",
  "end-date": "PVTF_...",
  "status": { ... },
  "issue-types": [
    {"name": "Epic", "id": "IT_...", "default": true},
    {"name": "Task", "id": "IT_..."},
    {"name": "Bug", "id": "IT_..."}
  ]
}
```

Issue types are optional. When absent, all type-related behavior is skipped.

## New CLI Subcommands

### `list-issue-types`

Category: repo-only (no config needed). Queries available issue types for a repository.

```
github-project-tools [--repo owner/repo] list-issue-types
```

GraphQL query:

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issueTypes(first: 50) { nodes { id name description } }
  }
}
```

Output: JSON array of `{id, name, description}` objects.

### `set-issue-type <issue-node-id> <type-id>`

Category: repo-only (no config needed). Sets the issue type via GraphQL mutation.

```
github-project-tools set-issue-type I_kwDO... IT_kwDO...
```

GraphQL mutation:

```graphql
mutation($id: ID!, $typeId: ID!) {
  updateIssue(input: { id: $id, issueTypeId: $typeId }) {
    issue { issueType { id name } }
  }
}
```

Output: the type name (via jq `.data.updateIssue.issue.issueType.name`).

## Enhanced issue-create

Add `--issue-type <name>` flag to `cmd_issue_create`. This requires access to config for type ID resolution, so the function signature changes:

```python
def cmd_issue_create(repo: str, args: list[str], config: GitHubProjectToolsConfig | None = None) -> int:
```

Dispatch in `main()` loads config optionally (not failing if absent):

```python
if subcmd == "issue-create":
    config = load_config(working_dir)  # None if missing
    return cmd_issue_create(resolved_repo, sub_args, config=config)
```

When `--issue-type <name>` is provided:

1. Validate config has `issue-types` configured. Error if not.
2. Match name case-insensitively against config entries.
3. Create the issue with `gh issue create` (existing logic).
4. Extract issue number from the returned URL.
5. Get node ID via `issue-view <number> --json id --jq '.id'` (internal call to `cmd_issue_view`).
6. Call `set-issue-type` internally (reuse the function, not a subprocess).

When `--issue-type` is not provided, behavior is unchanged.

The default type in config is a **skill-level concept** — the CLI does not auto-apply defaults. The skill decides whether to pass `--issue-type`.

## Skill Changes

### add-issue skill

Update Phase 3 step 1. When config has `issue-types` configured:

```bash
<cli> issue-create --title "<title>" --body "<body>" --issue-type "<default-type-name>"
```

The skill uses the default type from config without prompting the user. If the user explicitly specified a different type, use that instead.

Add `set-issue-type` to the skill's `allowed-tools` list:

```
Bash(*/github-project-tools/scripts/github-project-tools.sh set-issue-type *)
Bash(*/github-project-tools/scripts/github-project-tools.sh list-issue-types *)
```

### setup skill

Add a new step after project field configuration:

1. Query available types: `<cli> list-issue-types`
2. If the repo has issue types, present them to the user.
3. Ask which types to include in config and which is the default.
4. Write to `.claude-shim.json` under `fields.issue-types`.

If the repo has no issue types, skip this step.

## Command Inventory

All CLI commands the skills will invoke, with exact invocation patterns:

| Command | Used by | Notes |
|---------|---------|-------|
| `issue-create --title T --body B` | add-issue | Existing, no type |
| `issue-create --title T --body B --issue-type N` | add-issue | New flag |
| `list-issue-types` | setup | New subcommand |
| `set-issue-type <node-id> <type-id>` | standalone use | New subcommand |

The `issue-create --issue-type` flag handles type resolution and setting internally (calls `issue-view` + `set-issue-type` logic within the same process). Skills do not need to call `set-issue-type` separately when using `issue-create --issue-type`.

## Testing

- Unit tests for `IssueType` config model validation (default required when list non-empty)
- Unit tests for `--issue-type` flag parsing in `cmd_issue_create`
- Unit tests for `list-issue-types` and `set-issue-type` subcommands (mock GraphQL)
- Existing tests must continue to pass (issue-create without --issue-type)
