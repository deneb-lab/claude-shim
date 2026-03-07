# Quality Check Hook Plugin

## Architecture

- `hook/` — Python package (`quality_check_hook`), the PostToolUse hook implementation
  - `src/quality_check_hook/` — Source code: `main.py` (entry point), `config.py` (pydantic models), `matcher.py` (file pattern matching), `runner.py` (check execution), `gitignore.py` (gitignore-aware filtering)
  - `tests/` — Pytest test suite
- `hooks/hooks.json` — Claude Code hook registration (PostToolUse on Write/Edit/MultiEdit)
- `scripts/setup-quality-check-hook.sh` — Setup script called by the `setup-quality-check-hook` skill
- `skills/setup-quality-check-hook/` — User-facing skill for configuring quality checks

Python 3.12+, strict pyright, managed by `uv`. All commands run from `plugins/quality-check-hook/hook/`.

## Gotchas

- The hook strips `VIRTUAL_ENV` from subprocess env to avoid tool resolution conflicts

## Development

### Quality Checks

```bash
cd plugins/quality-check-hook/hook
uv run pytest -v
uv run ruff check
uv run ruff format --check
uv run pyright
```
