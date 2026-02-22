---
name: setup-quality-check-hook
description: Set up or modify .claude-shim.json quality checks for the current repository
---

# Quality Check Hook — Setup

Configure quality checks that run automatically when Claude edits files in this repository.

## How the Hook Works

Understanding the execution model is essential for writing correct commands.

**Trigger:** The hook runs on every `Write`, `Edit`, or `MultiEdit` tool use by Claude.

**Execution flow:**
1. The hook receives the edited file path from Claude
2. It checks if the file is gitignored (`git check-ignore -q`) — if yes, the file is skipped entirely
3. It reads `.claude-shim.json` from the repository root
4. It matches the file path against `include` patterns and collects commands
5. It checks `exclude` patterns — if the file matches any exclude, it is skipped
6. It runs each collected command as `{command} {file_path}` (file path appended as last argument)
7. Commands run in order. Execution stops on first failure (non-zero exit code)
8. On failure, the hook returns exit code 2, which blocks Claude from proceeding

**Command ordering principle:** Format first (rewrites file), then auto-fix (fixes lint issues in-place), then lint-check (fails if issues remain). This matters because:
- Formatters like `prettier --write` always exit 0 on success
- Auto-fixers like `eslint --fix` exit 0 even when some issues can't be auto-fixed
- A follow-up lint-only pass (`eslint`) catches remaining errors and fails the hook

**Gitignore handling:** Files in `.gitignore` are automatically skipped by the hook at runtime. This means:
- Do NOT add gitignored directories (like `node_modules` if it's in `.gitignore`) to the `exclude` list — it's redundant
- The `exclude` list is for directories/patterns that are NOT gitignored but should still skip quality checks (e.g., generated code that is committed to the repo)

**Timeouts:** Each command has a 30-second timeout. If a command exceeds this, it is killed and the hook fails.

## Prerequisites

Run `scripts/setup-quality-check-hook.sh check-uv` to verify that `uv` is installed.

If the command fails, stop and tell the user:

> The quality-check-hook plugin requires uv to run. Install it with:
> `curl -LsSf https://astral.sh/uv/install.sh | sh`
> See https://docs.astral.sh/uv/getting-started/installation/ for other methods.

Do not proceed until `uv` is available.

## Step 1: Check for Existing Config

Look for `.claude-shim.json` in the repository root.

- **If it exists:** Read it and present a menu using AskUserQuestion with these options:
  1. **Summarize current config** — Display the current `.claude-shim.json` in a human-readable format: what patterns are checked, what commands run for each, what's excluded. Then ask the user what they want to do next.
  2. **Scan for changes** — Re-run the detection from Step 2, compare results with current config, and present a diff: what tooling was added/removed, what commands changed, what excludes should be updated. Let the user approve or modify the suggested changes.
  3. **Full reconfigure** — Warn the user that this will overwrite the existing config, then proceed to Step 2 as if this were a first-time setup.
- **If it doesn't exist:** Proceed directly to Step 2 (no menu).

## Step 2: Detect Package Runner

Before detecting tooling, determine the JavaScript/TypeScript package runner from lockfiles:

| Lockfile | Runner |
|---|---|
| `bun.lockb` or `bun.lock` | `bunx` |
| `pnpm-lock.yaml` | `pnpx` |
| `yarn.lock` | `npx` |
| `package-lock.json` | `npx` |
| None of the above | `npx` |

Use the detected runner (referred to as `{runner}` below) in all JS/TS commands. Present it to the user for confirmation: "Detected `bun.lockb` — using `bunx` as the package runner. Change?"

## Step 3: Detect Project Tooling

Scan the repository for these markers and build a proposed config. **Detection order matters** — some tools are mutually exclusive:

| Marker | How to detect | Pattern | Default commands |
|---|---|---|---|
| **Biome** | `package.json` has `@biomejs/biome` in `dependencies` or `devDependencies` | `**/*.{js,jsx,ts,tsx}` | `{runner} biome check --fix`, `{runner} biome check` |
| **Prettier** | `package.json` has `prettier` in `dependencies` or `devDependencies` AND **Biome was NOT detected** | `**/*.{js,jsx,ts,tsx,md,css,json}` | `{runner} prettier --write` |
| **ESLint** | `package.json` has `eslint` in `dependencies` or `devDependencies` AND **Biome was NOT detected** | `**/*.{js,jsx,ts,tsx}` | `{runner} eslint --fix`, `{runner} eslint` |
| **Python (ruff)** | `pyproject.toml` exists AND has `ruff` in `[dependency-groups]`, `[project.dependencies]`, or `[project.optional-dependencies]` | `**/*.py` | `uv run ruff format`, `uv run ruff check --fix` |
| **Python (basic)** | `pyproject.toml` or `setup.py` or `requirements.txt` exists (and ruff NOT detected) | `**/*.py` | Ask user what Python tools they use |
| **Ansible** | `.ansible-lint` or `ansible.cfg` exists, OR both `roles/` and `playbooks/` directories exist | `**/*.{yaml,yml}` | `ansible-lint --fix`, `ansible-lint` |
| **YAML (yamllint)** | Any `*.yaml` or `*.yml` file exists (use Glob `**/*.{yaml,yml}`) AND **Ansible was NOT detected** | `**/*.{yaml,yml}` | `yamllint` |
| **Shell** | Any `*.sh` file exists (use Glob `**/*.sh`) | `**/*.sh` | `shellcheck` |
| **JSON** | Any `*.json` file exists (use Glob `**/*.json`) | `**/*.json` | `jq .` |

For `package.json` detection: read the file and check both `dependencies` and `devDependencies` objects for the tool name as a key.

### Config Path Detection

For Biome, Prettier, and ESLint — check if the tool's config file is in the repository root. If not, search common locations and include the appropriate flag:

**Biome:** Look for `biome.json` or `biome.jsonc` in repo root. If not found, search for it elsewhere (common: `.claude/hooks/`, `config/`). If found elsewhere, add `--config-path {dir}` to both Biome commands.

**Prettier:** Look for `.prettierrc`, `.prettierrc.json`, `.prettierrc.yml`, `.prettierrc.js`, `prettier.config.js`, `prettier.config.mjs` in repo root. If not found, search elsewhere. If found, add `--config {path}` to the Prettier command.

**ESLint:** Look for `.eslintrc`, `.eslintrc.json`, `.eslintrc.yml`, `.eslintrc.js`, `eslint.config.js`, `eslint.config.mjs` in repo root. If not found, search elsewhere. If found, add `--config {path}` to ESLint commands.

## Step 4: Build Exclude List

Build the exclude list using these candidates based on detected tooling:

**JS/TS candidates:** `node_modules`, `dist`, `build`, `.next`, `.nuxt`
**Python candidates:** `.venv`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`
**General candidates:** `coverage`, `.cache`

**For each candidate:**
1. Does this directory actually exist in the repo? → If no, skip it
2. Is it gitignored? (Check with `git check-ignore -q {dir}`) → If yes, skip it — the hook already skips gitignored files at runtime

Only include candidates that **exist AND are NOT gitignored**.

Tell the user: "Files matched by .gitignore are automatically skipped by the hook, so they don't need to be in the exclude list. The excludes below are only for non-gitignored directories you still want to skip."

## Step 5: Present Proposed Config

Show the user the proposed `.claude-shim.json` as formatted JSON. For each entry, explain:
- What was detected and why (e.g., "Found `@biomejs/biome` in package.json devDependencies")
- What each command does and the execution order
- The detected package runner (if applicable)
- Any non-root config paths detected

Ask the user to confirm, or tell you what to change. Iterate until they're satisfied.

The user may:
- Remove entries for languages they don't want checked
- Add entries for languages not auto-detected
- Change commands (e.g., add flags, change tools)
- Change patterns (e.g., exclude test files from formatting)
- Add or remove exclude patterns
- Override the package runner

## Step 6: Write Config

Write the final `.claude-shim.json` to the repository root:

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

> `.claude-shim.json` has been written. The quality-check-hook plugin will now automatically run these quality checks whenever Claude edits matching files.
>
> **Gitignored files are automatically skipped** — no need to add them to the exclude list.
>
> Re-run this skill anytime to review or update the configuration.
