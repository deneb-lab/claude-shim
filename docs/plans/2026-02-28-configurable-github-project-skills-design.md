# Configurable GitHub Project Skills

## Problem

The github-project-tools skills auto-detect project configuration (project ID, field IDs, status option mappings) on every invocation via `gh` CLI calls. This is fragile (hardcoded field names like "Status", always picks the first project) and slow (multiple API calls per skill run).

## Solution

Store project configuration in `.claude-shim.json` (shared config file already used by quality-check-hook). A new setup skill handles interactive detection and writes the config. The three existing skills read from config instead of auto-detecting.

## Config Shape

The `github-project-tools` section in `.claude-shim.json`:

```json
{
  "github-project-tools": {
    "project": "https://github.com/users/elahti/projects/1",
    "fields": {
      "start-date": "PVTF_xxx",
      "end-date": "PVTF_yyy",
      "status": {
        "id": "PVTF_zzz",
        "todo": { "name": "Todo", "option-id": "PVTO_1" },
        "in-progress": { "name": "In Progress", "option-id": "PVTO_2" },
        "done": { "name": "Done", "option-id": "PVTO_4" }
      }
    }
  }
}
```

Single project per config. Status maps three logical roles (`todo`, `in-progress`, `done`) to project-specific status names and GraphQL option IDs. Skills only set target statuses — they don't need to know the previous state or the full status flow.

### Pydantic Models

```python
class StatusMapping(BaseModel):
    name: str
    option_id: str = Field(alias="option-id")

class StatusField(BaseModel):
    id: str
    todo: StatusMapping
    in_progress: StatusMapping = Field(alias="in-progress")
    done: StatusMapping

class ProjectFields(BaseModel):
    start_date: str = Field(alias="start-date")
    end_date: str = Field(alias="end-date")
    status: StatusField

class GitHubProjectToolsConfig(BaseModel):
    project: str
    fields: ProjectFields
```

`load_config(cwd)` reads `.claude-shim.json`, extracts the `github-project-tools` key, validates with pydantic. Returns `None` if key is absent, raises `ValueError` on invalid data.

## Python Script (replacing `github-projects.sh`)

The shell script is replaced by a uv-managed Python package, following quality-check-hook's pattern.

### Structure

```
plugins/github-project-tools/
├── scripts/
│   └── github-projects.sh          # DELETED
├── hook/
│   ├── pyproject.toml               # uv project, deps: pydantic
│   ├── src/
│   │   └── github_project_tools/
│   │       ├── __init__.py
│   │       ├── config.py            # pydantic models + load_config()
│   │       └── cli.py              # subcommand dispatch, gh CLI calls
│   └── tests/
│       ├── test_config.py
│       └── test_cli.py
├── skills/
│   ├── add-issue/
│   ├── start-implementation/
│   ├── end-implementation/
│   └── setup-github-project-tools/  # NEW
└── .claude-plugin/
    └── plugin.json
```

### Invocation

Skills invoke the CLI via:

```bash
uv run --project <HOOK_PATH> python -m github_project_tools.cli <subcommand> [args...]
```

Same subcommand interface as the old shell script (`issue-view-full`, `set-status`, `set-date`, etc.), so skill prompts change minimally.

### What Changes in the CLI

Removed (read from config instead):
- `detect_project()` — project ID/number from config
- `detect_status_field()` — status field ID and option mappings from config
- `get-project-fields` subcommand — replaced by `read-config`

Kept:
- `detect_repo()` — still needed for `--repo` auto-detection fallback via git remote

New:
- `read-config` — reads `.claude-shim.json`, validates with pydantic, outputs the `github-project-tools` section as JSON (exit code 1 if missing/invalid)

## Setup Skill (`setup-github-project-tools`)

New SKILL.md prompt that handles interactive configuration.

### Flow

1. **Check for existing config** — Read `.claude-shim.json`, look for `github-project-tools` key.
   - If exists: show current config summary, ask "Reconfigure?" / "Keep current".
   - If absent (or file missing): proceed to detection.

2. **Detect project** — `gh project list --owner <owner>` to list available projects.
   - One project: auto-select, confirm with user.
   - Multiple projects: check which project current issues belong to via `gh issue list --repo <repo> --limit 5 --json number,projectItems` (single extra call). Recommend the project that issues are connected to. Present list with recommendation, user confirms.
   - No projects: error, tell user to create a project first.

3. **Detect field IDs** — Query the selected project's fields via `gh project field-list`.
   - Find date fields by name pattern ("Start date", "End date").
   - Find status field by name pattern ("Status").
   - Confirm with user. If auto-detection misses a field, ask user to pick from the full list.

4. **Detect status mappings** — Fetch status options from the status field.
   - Auto-match names to roles using common patterns:
     - `todo`: "Todo", "To Do", "Backlog", "New"
     - `in-progress`: "In Progress", "In progress", "Working", "Active"
     - `done`: "Done", "Complete", "Completed", "Shipped", "Closed"
   - Present proposed mapping for confirmation.
   - If any role unmatched, ask user to assign it manually.

5. **Write config** — Merge into `.claude-shim.json`:
   - File exists: read, add/replace `github-project-tools` key, write back.
   - File doesn't exist: create with just `github-project-tools` key.
   - Present final config for confirmation before writing.

6. **Confirm** — "Configuration saved."

## Changes to Existing Skills

### Shared Prompts

**`preflight.md`** (all 3 skills) — Glob changes from `**/github-projects.sh` to `**/github-project-tools/hook`. Stores resolved path as `HOOK_PATH`. All commands become `uv run --project <HOOK_PATH> python -m github_project_tools.cli <subcommand>`.

**`setup.md`** (start-implementation, end-implementation) — Replaced:
1. Run `<cli> read-config`.
2. If valid JSON: extract `START_FIELD`, `END_FIELD`, status info from config. Done.
3. If empty/error: tell user "No config found." Invoke `setup-github-project-tools` skill. After setup, re-run `read-config`.

**`conventions.md`** (all 3 skills) — Update invocation pattern example to `uv run --project` form.

### Skill-Specific

- `set-status` calls: same interface (`set-status <item> in-progress`), Python resolves option ID from config internally.
- `add-issue`: reads config instead of calling `get-project-fields`.
- `parse-issue-arg.md`: no change.

## Testing

### `test_config.py`

- Valid config with all fields returns typed config
- Missing `.claude-shim.json` returns `None`
- File exists but no `github-project-tools` key returns `None`
- Invalid status mapping (missing role) raises `ValueError`
- Invalid field IDs (wrong type) raises `ValueError`
- Extra keys in file (e.g., `quality-checks`) ignored

### `test_cli.py`

- `read-config` with valid config outputs JSON
- `read-config` with missing config exits with code 1
- `set-status <item> done` calls `gh` with correct option ID from config
- `set-date <item> <field-id>` calls `gh` with correct field ID
- `issue-view-full <number>` passes through to `gh`
- `--repo` override prepends repo to `gh` calls
- `preflight` checks `gh auth status`

### CI

```bash
cd plugins/github-project-tools/hook
uv run pytest -v
uv run ruff check
uv run ruff format --check
uv run pyright
```

Added as a new step in `.github/workflows/ci.yml`.
