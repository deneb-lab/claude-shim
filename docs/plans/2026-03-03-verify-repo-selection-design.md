# Verify Which Repo to Use — Design

Issue: [elahti/deneb-marketplace#70](https://github.com/elahti/deneb-marketplace/issues/70)

## Problem

The `setup-github-project-tools` skill detects and confirms the target repository with the user (Step 2), but never stores it in `.claude-shim.json`. This means:

- All operational skills (add-issue, start-impl, end-impl) auto-detect repo from the git remote every time
- When working from a different repo (e.g., `claude-shim` managing issues in `deneb-marketplace`), auto-detection picks the wrong repo
- `add-issue` has no mechanism to target a specific repo at all (no URL to parse)
- `start-implementation` and `end-implementation` only get the correct repo when the user passes a full issue URL

## Design

### 1. Config Model Change

Add optional `repo` field to `GitHubProjectToolsConfig` in `config.py`:

```python
class GitHubProjectToolsConfig(BaseModel):
    repo: str | None = None
    project: str
    fields: ProjectFields
```

Optional for backward compatibility — existing configs without it are valid but trigger a migration prompt in the skills.

Regenerate `claude-shim.schema.json` after updating the model.

### 2. Setup Skill Writes Repo to Config

`setup-github-project-tools` SKILL.md Step 6 (Write Config) includes `repo` in the JSON:

```json
{
  "github-project-tools": {
    "repo": "<REPO>",
    "project": "<PROJECT_URL>",
    "fields": { ... }
  }
}
```

No other changes to the setup skill — it already detects and confirms the repo in Step 2.

### 3. Shared Prompt (`setup.md`) Repo Check

After `read-config` succeeds, add a repo check:

1. Check if `repo` is present in the JSON output
2. **If present:** Use it as `REPO_OVERRIDE` for all subsequent CLI commands
3. **If missing:**
   - Detect current repo via `<cli> repo-detect`
   - Ask user: "No repository configured. Detected: `owner/repo`. Use this?"
     - Yes → save as REPO_OVERRIDE
     - No → user provides `owner/repo`
   - Read `.claude-shim.json`, add `repo` field to `github-project-tools` key, write back
   - Ask: "Commit the updated config?"
   - Use the new repo going forward

**Key rule:** Never continue without repo set.

### 4. URL Override Precedence

When `parse-issue-arg.md` extracts a repo from a full issue URL (e.g., `https://github.com/owner/repo/issues/42`), that URL-derived repo takes precedence over the config repo. The config repo is the default; URL is the explicit override.

## Code Review Findings

### `setup-github-project-tools`

1. **Main issue (this ticket):** Step 2 detects repo but doesn't store it
2. **Dead code in `cli.py:650`:** `repo_only_cmds` section calls `detect_repo(repo)` but the resolved value is never used by `cmd_get_parent`, `cmd_count_open_sub_issues`, or `cmd_set_parent`

### `setup-quality-check-hook`

No issues found. The skill is repo-agnostic and works correctly.

### Cross-cutting

3. **`add-issue` gap:** No mechanism for user to specify target repo. Fixed by reading repo from config via `setup.md`.
4. **Shared prompt sync:** `setup.md` is shared across add-issue, start-impl, and end-impl. Updating it once fixes all three. `preflight.md` and `conventions.md` also shared — no changes needed.

## Changes Summary

| File | Change |
|------|--------|
| `plugins/github-project-tools/hook/src/github_project_tools/config.py` | Add `repo: str \| None = None` to `GitHubProjectToolsConfig` |
| `plugins/github-project-tools/hook/src/github_project_tools/cli.py` | Remove dead `detect_repo` call in `repo_only_cmds` |
| `plugins/github-project-tools/hook/tests/test_config.py` | Add tests for config with/without `repo` field |
| `plugins/github-project-tools/hook/tests/test_cli.py` | Update test configs, add `read-config` test with repo |
| `plugins/quality-check-hook/claude-shim.schema.json` | Regenerate to include `repo` field |
| `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md` | Add `repo` to Step 6 config JSON |
| `plugins/github-project-tools/skills/add-issue/prompts/setup.md` | Add repo check after read-config |
| `plugins/github-project-tools/skills/start-implementation/prompts/setup.md` | Same (shared prompt) |
| `plugins/github-project-tools/skills/end-implementation/prompts/setup.md` | Same (shared prompt) |
