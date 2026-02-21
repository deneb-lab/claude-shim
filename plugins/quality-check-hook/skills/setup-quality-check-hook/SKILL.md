---
name: setup-quality-check-hook
description: Set up or modify .claude-shim.json quality checks for the current repository
---

# Quality Check Hook — Setup

Configure quality checks that run automatically when Claude edits files in this repository.

## Prerequisites

Check that `uv` is available:

```bash
which uv
```

If `uv` is not found, stop and tell the user:

> The quality-check-hook plugin requires uv to run. Install it with:
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
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
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

> `.claude-shim.json` has been created. The quality-check-hook plugin will now automatically run these quality checks whenever Claude edits matching files.
>
> You can re-run this skill anytime to modify the configuration.
