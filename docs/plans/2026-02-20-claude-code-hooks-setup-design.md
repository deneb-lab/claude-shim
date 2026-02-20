# Claude Code Hooks — Setup Skill & JSON Schema Design

**Goal:** Make the claude-code-hooks plugin easier to adopt by adding a JSON schema for editor validation and an interactive setup skill that auto-detects project tooling and generates `.claude-shim.json`.

## Components

### 1. JSON Schema

A static JSON Schema file at `plugins/claude-code-hooks/claude-shim.schema.json`, generated from the Pydantic models. Validates the `quality-checks` structure.

Every `.claude-shim.json` written by the skill includes a `$schema` reference:

```json
{
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json",
  "quality-checks": { ... }
}
```

The hook's `load_config` already ignores unknown keys, so `$schema` passes through without issues.

### 2. Setup Skill

Lives at `plugins/claude-code-hooks/skills/setup/SKILL.md`. Invoked via `claude-code-hooks:setup`.

**The skill is a prompt, not code.** It instructs Claude to do the detection and config generation using standard tools (Glob, Read, Write). No Python scripts needed.

#### Workflow

1. **Scan** repo root for project markers
2. **Present** detected languages and proposed config with default commands
3. **Let the user** confirm, modify commands, add/remove entries, change patterns
4. **Write** `.claude-shim.json` with `$schema` reference
5. If `.claude-shim.json` already exists, load and show current state — let user modify rather than overwrite

#### Auto-Detection Table

| Marker | Pattern | Default commands |
|---|---|---|
| `package.json` + prettier in deps | `**/*.{js,jsx,ts,tsx,md}` | `npx prettier --write` |
| `package.json` + eslint in deps | `**/*.{js,jsx,ts,tsx}` | `npx eslint --fix`, `npx eslint` |
| `pyproject.toml` | `**/*.py` | `uv run ruff format`, `uv run ruff check --fix` |
| `*.sh` exists | `**/*.sh` | `shellcheck` |
| `*.yaml`/`*.yml` exists | `**/*.{yaml,yml}` | `yamllint` |

**Command ordering principle:** format first, then auto-fix, then lint-check. Formatters exit 0 on success. Auto-fixers (like `eslint --fix`) exit 0 even when some issues remain unfixed, so a follow-up lint-only pass catches those.

#### Default Excludes

Populated based on detected languages:
- JS/TS projects: `node_modules`
- Python projects: `.venv`, `__pycache__`
- General: `dist`, `build`

The skill also peeks at `.gitignore` for additional exclude candidates.

#### Prerequisites Check

The skill checks if `uv` is on PATH before proceeding. If missing, it tells the user:

> The claude-code-hooks plugin requires uv to run. Install it with:
> `curl -LsSf https://astral.sh/uv/install.sh | sh`
> See https://docs.astral.sh/uv/getting-started/installation/ for other methods.

The skill does not proceed until uv is available.

#### Edge Cases

- **No markers found:** Tell the user, offer to create an empty config with just the schema reference for manual editing.
- **Tool not installed at runtime:** The hook command fails and Claude sees the error — this is designed behavior (fail closed). The skill doesn't verify tool availability beyond the uv prerequisite.
- **Existing config:** Load it, show current entries, let user add/remove/modify. Never silently overwrite.

### 3. Existing Hook Behavior (No Changes)

When `.claude-shim.json` doesn't exist, `load_config` returns `None` and the hook exits silently with code 0. Safe to install the plugin globally — repos without config are unaffected.
