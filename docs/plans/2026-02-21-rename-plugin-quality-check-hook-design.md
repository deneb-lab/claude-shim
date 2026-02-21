# Design: Rename claude-code-hooks → quality-check-hook

## Context

The `claude-code-hooks` plugin name is generic and doesn't describe what it does. Renaming to `quality-check-hook` makes the purpose self-evident. This is a comprehensive rename covering the plugin directory, Python package, skill, metadata, and all references.

## Scope

### Directory renames (via git mv)

| From | To |
|---|---|
| `plugins/claude-code-hooks/` | `plugins/quality-check-hook/` |
| `hook/src/claude_code_hooks/` | `hook/src/quality_check_hook/` |
| `skills/setup/` | `skills/setup-quality-check-hook/` |

### String replacements

| Old | New | Files |
|---|---|---|
| `"claude-code-hooks"` | `"quality-check-hook"` | plugin.json, marketplace.json, pyproject.toml |
| `claude_code_hooks` | `quality_check_hook` | All Python imports, hooks.json `-m` invocation, test mocks |
| `plugins/claude-code-hooks` | `plugins/quality-check-hook` | CI workflow, schema `$id`, generate_schema.py, SKILL.md |
| `claude-code-hooks:setup` | `quality-check-hook:setup-quality-check-hook` | Any skill cross-references |

### Files affected (~20)

1. `.claude-plugin/marketplace.json` — plugin name, source path, version bump
2. `.github/workflows/ci.yml` — 4 path references
3. `plugins/.../plugin.json` — name, version bump
4. `plugins/.../CLAUDE.md` — path references
5. `plugins/.../claude-shim.schema.json` — `$id` URL
6. `plugins/.../hooks/hooks.json` — `-m` invocation
7. `plugins/.../hook/pyproject.toml` — package name
8. `plugins/.../hook/scripts/generate_schema.py` — import path, schema URL
9. `plugins/.../hook/src/quality_check_hook/*.py` — 4 source files (imports)
10. `plugins/.../hook/tests/*.py` — 4 test files (imports, mocks)
11. `plugins/.../skills/setup-quality-check-hook/SKILL.md` — schema URL, skill name
12. Any docs/plans referencing old name

### Not changed

- Git tags (`claude-code-hooks/v0.1.0`, `v0.2.0`) — historical
- `uv.lock` — regenerated after pyproject.toml change
- Config file name `.claude-shim.json` — user-facing, unchanged
- Schema stays inside the plugin directory

### Version bumps

- Plugin version: `0.2.0` → `0.3.0` (breaking rename)
- Marketplace metadata version: `0.10.0` → `0.11.0`

## Verification

1. Run quality checks from the plugin's CLAUDE.md:
   ```bash
   cd plugins/quality-check-hook/hook
   uv run pytest -v
   uv run ruff check
   uv run ruff format --check
   uv run pyright
   ```
2. Regenerate schema to verify the script works with new paths:
   ```bash
   cd plugins/quality-check-hook/hook && uv run python scripts/generate_schema.py
   ```
3. Verify no stale references remain:
   ```bash
   grep -r "claude-code-hooks" --include='*.py' --include='*.json' --include='*.yml' --include='*.md' .
   grep -r "claude_code_hooks" --include='*.py' --include='*.json' --include='*.yml' --include='*.md' .
   ```
   (Only git tags and historical docs/plans should match)
