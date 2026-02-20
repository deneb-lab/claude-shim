# Claude Code Hooks — Setup Skill & JSON Schema Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a JSON schema for `.claude-shim.json` editor validation and an interactive setup skill that auto-detects project tooling and generates the config file.

**Architecture:** A static JSON Schema file generated from Pydantic models via a small script, plus a SKILL.md prompt that instructs Claude to scan repos, propose configs, and write `.claude-shim.json`. No new runtime Python code — the schema is a build artifact and the skill is pure prompt.

**Tech Stack:** Python (Pydantic schema export), JSON Schema Draft 2020-12, SKILL.md

**Design doc:** `docs/plans/2026-02-20-claude-code-hooks-setup-design.md`

---

### Task 1: Generate JSON Schema from Pydantic Models

Create a script that exports the Pydantic models as a JSON Schema file.

**Files:**
- Create: `plugins/claude-code-hooks/hook/scripts/generate_schema.py`
- Create: `plugins/claude-code-hooks/claude-shim.schema.json`

**Step 1: Write the schema generation script**

```python
"""Generate JSON Schema for .claude-shim.json from Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from claude_code_hooks.config import ClaudeShimConfig

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "claude-shim.schema.json"


def main() -> None:
    schema = ClaudeShimConfig.model_json_schema(
        mode="validation",
        by_alias=True,
    )

    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json"

    # Add top-level properties description
    if "properties" in schema and "quality-checks" in schema["properties"]:
        schema["properties"]["quality-checks"]["description"] = (
            "Quality check rules — which files to match and which commands to run"
        )

    # Allow $schema key in the config file
    schema["properties"]["$schema"] = {
        "type": "string",
        "description": "JSON Schema reference for editor validation",
    }

    SCHEMA_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Schema written to {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
```

**Step 2: Run the script to generate the schema**

Run: `cd plugins/claude-code-hooks/hook && uv run python scripts/generate_schema.py`

Expected: `plugins/claude-code-hooks/claude-shim.schema.json` is created.

**Step 3: Verify the schema is valid JSON Schema**

Run: `cd plugins/claude-code-hooks && cat claude-shim.schema.json | jq .`

Expected: Valid JSON with `$schema`, `$id`, `properties` containing `quality-checks` and `$schema`.

**Step 4: Run quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check scripts/ && uv run ruff format --check scripts/ && uv run pyright`

Fix any issues. The script must pass ruff and pyright.

**Step 5: Commit**

```bash
git add plugins/claude-code-hooks/hook/scripts/generate_schema.py plugins/claude-code-hooks/claude-shim.schema.json
git commit -m "feat(claude-code-hooks): add JSON schema for .claude-shim.json"
```

---

### Task 2: Update Config Module for $schema Passthrough

Verify the Pydantic model ignores the `$schema` key. Currently `ClaudeShimConfig` uses default Pydantic behavior which forbids extra fields in strict mode. Add a test to confirm and fix if needed.

**Files:**
- Modify: `plugins/claude-code-hooks/hook/tests/test_config.py`
- Possibly modify: `plugins/claude-code-hooks/hook/src/claude_code_hooks/config.py`

**Step 1: Write a test for $schema passthrough**

Add to `tests/test_config.py`:

```python
def test_schema_key_ignored(self, tmp_path: Path) -> None:
    config_data = {
        "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json",
        "quality-checks": {
            "include": [
                {"pattern": "**/*.py", "commands": ["ruff check"]}
            ]
        },
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(tmp_path)

    assert result is not None
    assert len(result.quality_checks.include) == 1
```

**Step 2: Run the test**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest tests/test_config.py::TestClaudeShimConfig::test_schema_key_ignored -v`

If it passes: Pydantic already ignores extra fields. Commit the test.

If it fails with a validation error: Add `model_config = ConfigDict(extra="ignore")` to `ClaudeShimConfig` in `config.py`, then re-run.

**Step 3: Run all tests and quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest -v && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run pyright`

Expected: all pass.

**Step 4: Commit**

```bash
git add plugins/claude-code-hooks/hook/tests/test_config.py plugins/claude-code-hooks/hook/src/claude_code_hooks/config.py
git commit -m "feat(claude-code-hooks): support \$schema key in config file"
```

---

### Task 3: Create the Setup Skill

Write the SKILL.md prompt that guides Claude through interactive setup of `.claude-shim.json`.

**Files:**
- Create: `plugins/claude-code-hooks/skills/setup/SKILL.md`

**Step 1: Create the skill file**

```markdown
---
name: setup
description: Set up or modify .claude-shim.json quality checks for the current repository
---

# Claude Code Hooks — Setup

Configure quality checks that run automatically when Claude edits files in this repository.

## Prerequisites

Check that `uv` is available:

```bash
which uv
```

If `uv` is not found, stop and tell the user:

> The claude-code-hooks plugin requires uv to run. Install it with:
> `curl -LsSf https://astral.sh/uv/install.sh | sh`
> See https://docs.astral.sh/uv/getting-started/installation/ for other methods.

Do not proceed until `uv` is available.

## Step 1: Check for Existing Config

Look for `.claude-shim.json` in the repository root.

- **If it exists:** Read it, show the current configuration to the user, and ask what they want to change (add entries, remove entries, modify commands, modify patterns, modify excludes).
- **If it doesn't exist:** Proceed to Step 2.

## Step 2: Detect Project Tooling

Scan the repository root for these markers and build a proposed config:

| Marker | How to detect | Pattern | Default commands |
|---|---|---|---|
| TypeScript/JavaScript with Prettier | `package.json` exists AND (`prettier` in `devDependencies` or `dependencies`) | `**/*.{js,jsx,ts,tsx,md}` | `npx prettier --write` |
| TypeScript/JavaScript with ESLint | `package.json` exists AND (`eslint` in `devDependencies` or `dependencies`) | `**/*.{js,jsx,ts,tsx}` | `npx eslint --fix`, `npx eslint` |
| Python | `pyproject.toml` exists | `**/*.py` | `uv run ruff format`, `uv run ruff check --fix` |
| Shell scripts | Any `*.sh` file exists in the repo (use Glob `**/*.sh`) | `**/*.sh` | `shellcheck` |
| YAML | Any `*.yaml` or `*.yml` file exists in the repo (use Glob `**/*.{yaml,yml}`) | `**/*.{yaml,yml}` | `yamllint` |

For JavaScript/TypeScript detection, read `package.json` and check both `dependencies` and `devDependencies` for the tool names.

**Command ordering principle:** Format first (rewrites file), then auto-fix (fixes lint issues in-place), then lint-check (fails if issues remain). This matters because:
- Formatters like `prettier --write` always exit 0 on success
- Auto-fixers like `eslint --fix` exit 0 even when some issues can't be auto-fixed
- A follow-up lint-only pass (`eslint`) catches remaining errors and fails the hook

## Step 3: Build Default Excludes

Based on what was detected, propose these excludes:

- JS/TS detected: `node_modules`
- Python detected: `.venv`, `__pycache__`
- Always include: `dist`, `build` (if those directories exist)

Also check `.gitignore` for additional common directories to exclude.

## Step 4: Present Proposed Config

Show the user the proposed `.claude-shim.json` as formatted JSON. Explain:
- What was detected and why
- What each command does
- That they can modify any entry before writing

Ask the user to confirm, or tell you what to change. Iterate until they're satisfied.

The user may:
- Remove entries for languages they don't want checked
- Add entries for languages not auto-detected
- Change commands (e.g., use `biome` instead of `prettier`)
- Change patterns (e.g., exclude test files)
- Add or remove exclude patterns

## Step 5: Write Config

Write the final `.claude-shim.json` to the repository root with this structure:

```json
{
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json",
  "quality-checks": {
    "include": [
      ...
    ],
    "exclude": [
      ...
    ]
  }
}
```

After writing, tell the user:

> `.claude-shim.json` has been created. The claude-code-hooks plugin will now automatically run these quality checks whenever Claude edits matching files.
>
> You can re-run this skill anytime to modify the configuration.
```

**Step 2: Verify the skill file has correct frontmatter**

Read back the file and confirm it starts with `---` YAML frontmatter containing `name: setup` and `description`.

**Step 3: Commit**

```bash
git add plugins/claude-code-hooks/skills/setup/SKILL.md
git commit -m "feat(claude-code-hooks): add setup skill for interactive config generation"
```

---

### Task 4: Update Plugin Metadata and Marketplace

Register the new skill in the plugin and bump versions.

**Files:**
- Modify: `plugins/claude-code-hooks/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

**Step 1: Bump plugin version to 0.2.0**

In `plugins/claude-code-hooks/.claude-plugin/plugin.json`, change `"version": "0.1.0"` to `"version": "0.2.0"`.

**Step 2: Update marketplace.json**

In `.claude-plugin/marketplace.json`:
- Change the `claude-code-hooks` entry's `"version"` from `"0.1.0"` to `"0.2.0"`
- Bump `metadata.version` from `"0.9.0"` to `"0.10.0"`

**Step 3: Update README.md**

In the Claude Code Hooks section of `README.md`, add after the **Requires** line:

```markdown
**Skills:**
- `claude-code-hooks:setup` — Detect project tooling and generate `.claude-shim.json` interactively
```

**Step 4: Validate JSON files**

Run: `for f in .claude-plugin/marketplace.json plugins/claude-code-hooks/.claude-plugin/plugin.json; do echo "Checking $f..."; jq . "$f" > /dev/null; done`

Expected: all valid.

**Step 5: Commit**

```bash
git add plugins/claude-code-hooks/.claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "Release claude-code-hooks v0.2.0: add setup skill and JSON schema"
```

---

### Task 5: Final Verification

Run all checks end-to-end.

**Step 1: Run all Python tests**

Run: `cd plugins/claude-code-hooks/hook && uv run pytest -v`

Expected: all tests pass (28 existing + 1 new = 29).

**Step 2: Run all Python quality checks**

Run: `cd plugins/claude-code-hooks/hook && uv run ruff check && uv run ruff format --check && uv run pyright`

Expected: all clean.

**Step 3: Validate all JSON files**

Run: `for f in $(find . -name '*.json' -not -path './.git/*' -not -path '*/.venv/*' -not -path '*/node_modules/*'); do echo "Checking $f..."; jq . "$f" > /dev/null; done`

Expected: all valid, including the new `claude-shim.schema.json`.

**Step 4: Verify plugin structure**

Confirm these new files exist:
- `plugins/claude-code-hooks/claude-shim.schema.json`
- `plugins/claude-code-hooks/hook/scripts/generate_schema.py`
- `plugins/claude-code-hooks/skills/setup/SKILL.md`

**Step 5: Verify schema content**

Read `plugins/claude-code-hooks/claude-shim.schema.json` and confirm it contains:
- `$schema` pointing to JSON Schema Draft 2020-12
- `$id` pointing to the raw GitHub URL
- `properties` with `$schema` and `quality-checks`
- `quality-checks` containing `include` (array of objects with `pattern` and `commands`) and `exclude` (array of strings)
