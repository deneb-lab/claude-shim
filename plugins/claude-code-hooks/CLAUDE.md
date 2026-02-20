# Claude Code Hooks Plugin

## Development

### JSON Schema

The file `claude-shim.schema.json` is generated from the Pydantic models in `hook/src/claude_code_hooks/config.py`.

**When you modify the config models, regenerate the schema:**

```bash
cd plugins/claude-code-hooks/hook && uv run python scripts/generate_schema.py
```

Commit the updated `claude-shim.schema.json` alongside your model changes.

### Quality Checks

```bash
cd plugins/claude-code-hooks/hook
uv run pytest -v
uv run ruff check
uv run ruff format --check
uv run pyright
```
