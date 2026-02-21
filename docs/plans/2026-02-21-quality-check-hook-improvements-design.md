# Quality Check Hook Improvements — Design

## Problem

The setup skill (`setup-quality-check-hook`) has a narrow detection table that fails on real-world projects. When tested against the [deneb](https://github.com/elahti/deneb) repo (Ansible + Biome + JSON), it missed most tooling, proposed non-existent directories as excludes, and didn't account for `.gitignore`. See [issue #1](https://github.com/elahti/claude-shim/issues/1) for full findings.

## Goals

1. Hook runtime respects `.gitignore` — never run quality checks on gitignored files
2. Setup skill auto-detects a much wider range of tooling (Biome, Ansible, JSON, package runners)
3. Setup skill only suggests excludes for directories that exist AND are not gitignored
4. Setup skill works for both first-run and re-run scenarios
5. Setup skill embeds all knowledge about how the hook works (no runtime discovery)

## Design

### 1. Hook Runtime — Gitignore Check

Add gitignore checking to the hook runtime using `git check-ignore -q <file_path>`.

**New function** in `matcher.py` (or new `gitignore.py`):

```python
def is_gitignored(file_path: str, cwd: str) -> bool:
    """Check if a file is ignored by .gitignore using git check-ignore."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", file_path],
            cwd=cwd,
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False  # fail open — if git isn't available, proceed normally
```

**Integration in `main.py`** — check after computing `relative_path`, before loading config:

```
1. Extract file_path from payload
2. Compute relative_path
3. NEW: if is_gitignored(file_path, cwd) → return early (exit 0)
4. Load config, collect commands, run them
```

**Edge cases:**
- Not a git repo → `git check-ignore` fails → treat as not ignored (proceed)
- git not installed → `FileNotFoundError` → treat as not ignored (proceed)
- Timeout → treat as not ignored (fail open)

### 2. Setup Skill — Expanded Detection Table

The detection table is the skill's embedded knowledge of how to detect project tooling. The skill scans in this order (priority matters — Biome before Prettier/ESLint, Ansible before yamllint):

| Marker | How to detect | Pattern | Default commands |
|---|---|---|---|
| **Biome** | `package.json` has `@biomejs/biome` in deps/devDeps | `**/*.{js,jsx,ts,tsx}` | `{runner} biome check --fix`, `{runner} biome check` |
| **Prettier** | `package.json` has `prettier` in deps/devDeps (AND Biome NOT detected) | `**/*.{js,jsx,ts,tsx,md,css,json}` | `{runner} prettier --write` |
| **ESLint** | `package.json` has `eslint` in deps/devDeps (AND Biome NOT detected) | `**/*.{js,jsx,ts,tsx}` | `{runner} eslint --fix`, `{runner} eslint` |
| **Python (ruff)** | `pyproject.toml` exists AND has `ruff` in deps | `**/*.py` | `uv run ruff format`, `uv run ruff check --fix` |
| **Python (basic)** | `pyproject.toml` exists (no ruff) | `**/*.py` | Ask user what tools they use |
| **Ansible** | `.ansible-lint` or `ansible.cfg` exists, or `roles/` + `playbooks/` dirs | `**/*.{yaml,yml}` | `ansible-lint --fix`, `ansible-lint` |
| **YAML (yamllint)** | Any `*.yaml`/`*.yml` exists (AND Ansible NOT detected) | `**/*.{yaml,yml}` | `yamllint` |
| **Shell** | Any `*.sh` file exists | `**/*.sh` | `shellcheck` |
| **JSON** | Any `*.json` file exists | `**/*.json` | `jq .` |

### 3. Package Runner Detection

Detect the JS/TS package runner from lockfiles:

| Lockfile | Runner |
|---|---|
| `bun.lockb` or `bun.lock` | `bunx` |
| `pnpm-lock.yaml` | `pnpx` |
| `yarn.lock` or `package-lock.json` or none | `npx` |

`{runner}` in the detection table is replaced with the detected runner. The skill presents the detected runner to the user for confirmation.

### 4. Config Path Detection

For tools that support non-root config files (Biome, Prettier, ESLint), the skill:

1. Checks if the tool's config file is in the repo root (e.g., `biome.json`, `.prettierrc`, `.eslintrc.*`)
2. If not found in root, searches common locations (`.claude/hooks/`, `config/`, etc.)
3. If found elsewhere, includes the appropriate flag in the command (e.g., `--config-path .claude/hooks`)

### 5. Smart Exclude Suggestions

**Candidate list by detected tooling:**

- **JS/TS:** `node_modules`, `dist`, `build`, `.next`, `.nuxt`
- **Python:** `.venv`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`
- **General:** `coverage`, `.cache`

**Filter logic for each candidate:**

1. Does it exist in the repo? → No → don't suggest
2. Is it gitignored? (`git check-ignore -q <dir>`) → Yes → don't suggest

Only directories that exist AND are not gitignored are suggested.

The skill explains: "Files matched by .gitignore are automatically skipped by the hook, so they don't need to be in the exclude list."

### 6. First-Run vs Re-Run

**First run** (no `.claude-shim.json`):
- Execute the full setup workflow: detect → propose → confirm → write
- No menu

**Re-run** (`.claude-shim.json` exists):
- Present a menu:
  1. **Summarize current config** — Display current config in human-readable format
  2. **Scan for changes** — Re-run detection, diff against current config, suggest updates
  3. **Full reconfigure** — Start fresh (warn about overwrite)

### 7. Embedded Hook Knowledge

The skill must contain all necessary knowledge about how the hook works so Claude doesn't need to read source code. The skill must document:

- **Execution model:** Each command runs as `{command} {file_path}` — the edited file path is appended as the last argument
- **Command ordering:** Format first (rewrites file), then auto-fix (fixes lint issues), then lint-check (fails if issues remain)
- **Failure behavior:** Execution stops on first command failure (non-zero exit code). Exit code 2 blocks Claude from proceeding.
- **Gitignore handling:** Files in .gitignore are automatically skipped by the hook at runtime — no need to add them to the exclude list
- **Exclude behavior:** Excludes in `.claude-shim.json` are for directories/patterns that are NOT gitignored but should still skip quality checks
- **Timeout:** Each command has a 30-second timeout

## Files Changed

### Modified

1. **`hook/src/quality_check_hook/main.py`** — Add gitignore check before command collection
2. **`hook/src/quality_check_hook/matcher.py`** (or new `gitignore.py`) — Add `is_gitignored()` function
3. **`hook/tests/`** — New tests for gitignore behavior
4. **`skills/setup-quality-check-hook/SKILL.md`** — Complete rewrite

### Unchanged

- `config.py` — Schema stays the same
- `runner.py` — Command execution unchanged
- `claude-shim.schema.json` — No schema changes
