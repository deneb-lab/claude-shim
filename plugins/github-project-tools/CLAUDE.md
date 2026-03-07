# GitHub Project Tools Plugin

## Architecture

- `hook/` — Python uv package: CLI that reads `.claude-shim.json` config (pydantic models) for use by skills
- `skills/` — Five skills: `add-issue`, `start-implementing-issue`, `end-implementing-issue`, `mass-update-issues`, `setup-github-project-tools`
- Each skill has a `prompts/` directory with prompt files
- `scripts/github-project-tools.sh` — GitHub CLI wrapper for project operations
- Configuration stored in `.claude-shim.json` (per-repository)

## Shared Prompts

`preflight.md` and `conventions.md` are duplicated across all 5 skills. `setup.md` is shared between `add-issue`, `start-implementing-issue`, `end-implementing-issue`, and `mass-update-issues`. `parse-issue-arg.md` is shared between `start-implementing-issue`, `end-implementing-issue`, and `mass-update-issues`. When editing, update ALL copies and verify with `git diff`. CI enforces sync.

## Development

```bash
cd plugins/github-project-tools/hook
uv run pytest -v
uv run ruff check
uv run ruff format --check
uv run pyright
```
