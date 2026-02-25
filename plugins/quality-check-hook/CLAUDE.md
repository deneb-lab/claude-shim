# Quality Check Hook Plugin

## Architecture

- `hook/` — Python package (`quality_check_hook`), the PostToolUse hook implementation
  - `src/quality_check_hook/` — Source code (config models, main entry point)
  - `tests/` — Pytest test suite
  - `scripts/generate_schema.py` — Schema generator for `claude-shim.schema.json`
- `hooks/hooks.json` — Claude Code hook registration (PostToolUse on Write/Edit/MultiEdit)
- `scripts/setup-quality-check-hook.sh` — Setup script called by the `setup-quality-check-hook` skill
- `skills/setup-quality-check-hook/` — User-facing skill for configuring quality checks
- `claude-shim.schema.json` — JSON Schema for `.claude-shim.json` config files (generated)

Python 3.12+, strict pyright, managed by `uv`. All commands run from `plugins/quality-check-hook/hook/`.

## Gotchas

- The hook strips `VIRTUAL_ENV` from subprocess env to avoid tool resolution conflicts

## Development

### JSON Schema

The file `claude-shim.schema.json` is generated from the Pydantic models in `hook/src/quality_check_hook/config.py`.

**When you modify the config models, regenerate the schema:**

```bash
cd plugins/quality-check-hook/hook && uv run python scripts/generate_schema.py
```

Commit the updated `claude-shim.schema.json` alongside your model changes.

### Quality Checks

```bash
cd plugins/quality-check-hook/hook
uv run pytest -v
uv run ruff check
uv run ruff format --check
uv run pyright
```
