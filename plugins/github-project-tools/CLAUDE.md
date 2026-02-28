# GitHub Project Tools Plugin

## Architecture

- `hook/` — Python uv package (CLI + pydantic config models)
- `skills/` — Four skills: `add-issue`, `start-implementation`, `end-implementation`, `setup-github-project-tools`
- Each skill has a `prompts/` directory with prompt files
- Configuration stored in `.claude-shim.json` (per-repository)

## Shared Prompts

`preflight.md` and `conventions.md` are duplicated across all 4 skills. `setup.md` is shared between `add-issue`, `start-implementation`, and `end-implementation`. `parse-issue-arg.md` is shared between `start-implementation` and `end-implementation`. When editing, update ALL copies and verify with `git diff`. CI enforces sync.

## Development

```bash
cd plugins/github-project-tools/hook
uv run pytest -v
uv run ruff check
uv run ruff format --check
uv run pyright
```
