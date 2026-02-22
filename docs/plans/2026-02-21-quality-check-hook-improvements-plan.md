# Quality Check Hook Improvements — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the quality-check-hook respect .gitignore at runtime and overhaul the setup skill with wider tooling detection, smart excludes, and re-run support.

**Architecture:** Two independent changes: (1) add a `is_gitignored()` check in the Python hook runtime using `git check-ignore -q`, inserted before command collection; (2) rewrite the setup skill SKILL.md with an expanded detection table, package runner detection, config path detection, smart exclude logic, and first-run vs re-run branching.

**Tech Stack:** Python 3.12, pydantic, wcmatch, pytest, subprocess (`git check-ignore`), Markdown (SKILL.md)

---

### Task 1: Add `is_gitignored()` function — test

**Files:**
- Create: `plugins/quality-check-hook/hook/src/quality_check_hook/gitignore.py`
- Test: `plugins/quality-check-hook/hook/tests/test_gitignore.py`

**Step 1: Write the failing tests**

Create `plugins/quality-check-hook/hook/tests/test_gitignore.py`:

```python
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from quality_check_hook.gitignore import is_gitignored


class TestIsGitignored:
    def test_ignored_file_returns_true(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert is_gitignored("/repo/node_modules/pkg/index.js", cwd="/repo") is True

    def test_tracked_file_returns_false(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert is_gitignored("/repo/src/app.ts", cwd="/repo") is False

    def test_git_not_installed_returns_false(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            assert is_gitignored("/repo/src/app.ts", cwd="/repo") is False

    def test_timeout_returns_false(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            assert is_gitignored("/repo/src/app.ts", cwd="/repo") is False

    def test_not_a_git_repo_returns_false(self) -> None:
        """git check-ignore returns 128 when not in a git repo."""
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128)
            assert is_gitignored("/tmp/file.ts", cwd="/tmp") is False

    def test_passes_correct_args_to_subprocess(self) -> None:
        with patch("quality_check_hook.gitignore.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            is_gitignored("/repo/src/app.ts", cwd="/repo")
            mock_run.assert_called_once_with(
                ["git", "check-ignore", "-q", "/repo/src/app.ts"],
                cwd="/repo",
                capture_output=True,
                timeout=5,
            )
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/quality-check-hook/hook && uv run pytest tests/test_gitignore.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quality_check_hook.gitignore'`

---

### Task 2: Add `is_gitignored()` function — implementation

**Files:**
- Create: `plugins/quality-check-hook/hook/src/quality_check_hook/gitignore.py`

**Step 1: Write the implementation**

Create `plugins/quality-check-hook/hook/src/quality_check_hook/gitignore.py`:

```python
from __future__ import annotations

import subprocess

GITIGNORE_CHECK_TIMEOUT_SECONDS = 5


def is_gitignored(file_path: str, *, cwd: str) -> bool:
    """Check if a file is ignored by .gitignore using git check-ignore.

    Returns True if the file is gitignored, False otherwise.
    Fails open: if git is unavailable or times out, returns False
    so quality checks still run.
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", file_path],
            cwd=cwd,
            capture_output=True,
            timeout=GITIGNORE_CHECK_TIMEOUT_SECONDS,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

**Step 2: Run tests to verify they pass**

Run: `cd plugins/quality-check-hook/hook && uv run pytest tests/test_gitignore.py -v`
Expected: All 6 tests PASS

**Step 3: Run full quality checks**

Run: `cd plugins/quality-check-hook/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 4: Commit**

```bash
git add plugins/quality-check-hook/hook/src/quality_check_hook/gitignore.py plugins/quality-check-hook/hook/tests/test_gitignore.py
git commit -m "feat(quality-check-hook): add is_gitignored() using git check-ignore"
```

---

### Task 3: Integrate gitignore check into main.py — test

**Files:**
- Modify: `plugins/quality-check-hook/hook/tests/test_main.py`

**Step 1: Write the failing tests**

Add to the `TestHandleHook` class in `plugins/quality-check-hook/hook/tests/test_main.py`:

```python
def test_gitignored_file_skipped(self, tmp_path: Path) -> None:
    """Gitignored files should be skipped even if they match a pattern."""
    config = {
        "quality-checks": {
            "include": [{"pattern": "**/*.ts", "commands": ["eslint"]}]
        }
    }
    (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
    test_file = tmp_path / "generated" / "types.ts"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("content")
    payload = self._make_payload(str(test_file), str(tmp_path))

    with (
        patch("quality_check_hook.main.is_gitignored", return_value=True),
        patch("quality_check_hook.runner.subprocess.run") as mock_run,
    ):
        exit_code, _stdout, stderr = handle_hook(json.dumps(payload))

    assert exit_code == 0
    assert stderr == ""
    assert mock_run.call_count == 0

def test_non_gitignored_file_checked(self, tmp_path: Path) -> None:
    """Non-gitignored files should proceed through normal quality checks."""
    config = {
        "quality-checks": {
            "include": [{"pattern": "**/*.ts", "commands": ["eslint"]}]
        }
    }
    (tmp_path / ".claude-shim.json").write_text(json.dumps(config))
    test_file = tmp_path / "src" / "app.ts"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("content")
    payload = self._make_payload(str(test_file), str(tmp_path))

    with (
        patch("quality_check_hook.main.is_gitignored", return_value=False),
        patch("quality_check_hook.runner.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        exit_code, _stdout, _stderr = handle_hook(json.dumps(payload))

    assert exit_code == 0
    assert mock_run.call_count == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/quality-check-hook/hook && uv run pytest tests/test_main.py::TestHandleHook::test_gitignored_file_skipped tests/test_main.py::TestHandleHook::test_non_gitignored_file_checked -v`
Expected: FAIL — `is_gitignored` is not imported in `main.py` yet

---

### Task 4: Integrate gitignore check into main.py — implementation

**Files:**
- Modify: `plugins/quality-check-hook/hook/src/quality_check_hook/main.py:1-9` (add import)
- Modify: `plugins/quality-check-hook/hook/src/quality_check_hook/main.py:38-41` (add check after relative_path)

**Step 1: Add import**

In `main.py`, add to the imports (after line 8):

```python
from quality_check_hook.gitignore import is_gitignored
```

**Step 2: Add gitignore check**

In `main.py`, after the `relative_path` computation (line 39) and before `commands = collect_commands(...)` (line 43), add:

```python
    if is_gitignored(file_path, cwd=cwd):
        return 0, "{}", ""
```

The full flow in `handle_hook` becomes:
1. Extract file_path
2. Load config
3. Compute relative_path
4. **Check gitignore → skip if ignored**
5. Collect commands
6. Run commands

**Step 3: Run the new tests to verify they pass**

Run: `cd plugins/quality-check-hook/hook && uv run pytest tests/test_main.py::TestHandleHook::test_gitignored_file_skipped tests/test_main.py::TestHandleHook::test_non_gitignored_file_checked -v`
Expected: PASS

**Step 4: Run full quality checks**

Run: `cd plugins/quality-check-hook/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 5: Commit**

```bash
git add plugins/quality-check-hook/hook/src/quality_check_hook/main.py plugins/quality-check-hook/hook/tests/test_main.py
git commit -m "feat(quality-check-hook): skip gitignored files at hook runtime"
```

---

### Task 5: Rewrite setup skill SKILL.md

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md`

**Step 1: Replace the entire SKILL.md content**

Write the new SKILL.md with this content:

````markdown
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
````

**Step 2: Review the SKILL.md for completeness**

Verify the SKILL.md covers all points from the design:
- [ ] Hook execution model documented (command + file_path, ordering, failure, timeout)
- [ ] Gitignore handling documented (automatic skip, don't add to excludes)
- [ ] Biome detection (with priority over Prettier/ESLint)
- [ ] Ansible detection (with priority over yamllint)
- [ ] JSON detection
- [ ] Package runner detection (bun/pnpm/yarn/npm)
- [ ] Config path detection (non-root configs)
- [ ] Smart excludes (existence check + gitignore check)
- [ ] First-run flow (direct to setup)
- [ ] Re-run flow (3-option menu)

**Step 3: Commit**

```bash
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): rewrite setup skill with expanded detection and gitignore support"
```

---

### Task 6: Final verification

**Step 1: Run full quality checks on the hook**

Run: `cd plugins/quality-check-hook/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 2: Verify no untracked files or missed changes**

Run: `git status`
Expected: Clean working tree

**Step 3: Review commit log**

Run: `git log --oneline -5`
Expected: Three new commits on top of existing work:
1. `feat(quality-check-hook): add is_gitignored() using git check-ignore`
2. `feat(quality-check-hook): skip gitignored files at hook runtime`
3. `feat(quality-check-hook): rewrite setup skill with expanded detection and gitignore support`
