# Rename claude-code-hooks → quality-check-hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the `claude-code-hooks` plugin to `quality-check-hook` across all directories, Python packages, metadata, CI, and references.

**Architecture:** Mechanical rename in three phases: (1) git mv directories + update all Python internals, (2) update all config/metadata/CI references, (3) version bump and release commit. Schema stays inside the plugin directory.

**Tech Stack:** Python (uv), Pydantic, git, GitHub Actions CI

**Design doc:** `docs/plans/2026-02-21-rename-plugin-quality-check-hook-design.md`

---

### Task 1: Git mv all directories

**Files:**
- Rename: `plugins/claude-code-hooks/` → `plugins/quality-check-hook/`
- Rename: `plugins/quality-check-hook/hook/src/claude_code_hooks/` → `plugins/quality-check-hook/hook/src/quality_check_hook/`
- Rename: `plugins/quality-check-hook/skills/setup/` → `plugins/quality-check-hook/skills/setup-quality-check-hook/`

**Step 1: Rename the plugin directory**

```bash
git mv plugins/claude-code-hooks plugins/quality-check-hook
```

**Step 2: Rename the Python package directory**

```bash
git mv plugins/quality-check-hook/hook/src/claude_code_hooks plugins/quality-check-hook/hook/src/quality_check_hook
```

**Step 3: Rename the skill directory**

```bash
git mv plugins/quality-check-hook/skills/setup plugins/quality-check-hook/skills/setup-quality-check-hook
```

---

### Task 2: Update Python source imports

**Files:**
- Modify: `plugins/quality-check-hook/hook/src/quality_check_hook/main.py:7-9`
- Modify: `plugins/quality-check-hook/hook/src/quality_check_hook/matcher.py:5`

**Step 1: Update main.py imports**

In `plugins/quality-check-hook/hook/src/quality_check_hook/main.py`, replace all three import lines:

```python
# Old (lines 7-9):
from claude_code_hooks.config import load_config
from claude_code_hooks.matcher import collect_commands
from claude_code_hooks.runner import run_commands

# New:
from quality_check_hook.config import load_config
from quality_check_hook.matcher import collect_commands
from quality_check_hook.runner import run_commands
```

**Step 2: Update matcher.py import**

In `plugins/quality-check-hook/hook/src/quality_check_hook/matcher.py`, line 5:

```python
# Old:
from claude_code_hooks.config import QualityChecks

# New:
from quality_check_hook.config import QualityChecks
```

Note: `config.py` and `runner.py` have no internal package imports — no changes needed.

---

### Task 3: Update Python test imports and mock paths

**Files:**
- Modify: `plugins/quality-check-hook/hook/tests/test_config.py:6`
- Modify: `plugins/quality-check-hook/hook/tests/test_main.py:5,52,69,109`
- Modify: `plugins/quality-check-hook/hook/tests/test_matcher.py:1-2`
- Modify: `plugins/quality-check-hook/hook/tests/test_runner.py:5,13,24,40,55,70`

**Step 1: Update test_config.py**

Line 6 — change import:

```python
# Old:
from claude_code_hooks.config import load_config
# New:
from quality_check_hook.config import load_config
```

**Step 2: Update test_main.py**

Line 5 — change import:

```python
# Old:
from claude_code_hooks.main import handle_hook
# New:
from quality_check_hook.main import handle_hook
```

Lines 52, 69, 109 — change mock target (use replace_all for `claude_code_hooks.runner.subprocess.run`):

```python
# Old:
with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
# New:
with patch("quality_check_hook.runner.subprocess.run") as mock_run:
```

**Step 3: Update test_matcher.py**

Lines 1-2:

```python
# Old:
from claude_code_hooks.config import QualityCheckEntry, QualityChecks
from claude_code_hooks.matcher import collect_commands
# New:
from quality_check_hook.config import QualityCheckEntry, QualityChecks
from quality_check_hook.matcher import collect_commands
```

**Step 4: Update test_runner.py**

Line 5 — change import:

```python
# Old:
from claude_code_hooks.runner import run_commands
# New:
from quality_check_hook.runner import run_commands
```

Lines 13, 24, 40, 55, 70 — change mock target (use replace_all for `claude_code_hooks.runner.subprocess.run`):

```python
# Old:
with patch("claude_code_hooks.runner.subprocess.run") as mock_run:
# New:
with patch("quality_check_hook.runner.subprocess.run") as mock_run:
```

---

### Task 4: Update hooks.json command invocation

**Files:**
- Modify: `plugins/quality-check-hook/hooks/hooks.json:10`

**Step 1: Update the -m module reference**

```json
// Old:
"command": "uv run --project \"${CLAUDE_PLUGIN_ROOT}/hook\" python -m claude_code_hooks.main"
// New:
"command": "uv run --project \"${CLAUDE_PLUGIN_ROOT}/hook\" python -m quality_check_hook.main"
```

---

### Task 5: Update pyproject.toml and regenerate uv.lock

**Files:**
- Modify: `plugins/quality-check-hook/hook/pyproject.toml:2`

**Step 1: Update package name**

```toml
# Old:
name = "claude-code-hooks"
# New:
name = "quality-check-hook"
```

**Step 2: Regenerate uv.lock**

```bash
cd plugins/quality-check-hook/hook && uv lock
```

---

### Task 6: Run tests to verify Python rename

**Step 1: Run pytest**

```bash
cd plugins/quality-check-hook/hook && uv run pytest -v
```

Expected: All 33 tests pass.

**Step 2: Run linting and type checking**

```bash
cd plugins/quality-check-hook/hook && uv run ruff check && uv run ruff format --check && uv run pyright
```

Expected: All pass.

**Step 3: Commit the Python rename**

```bash
git add plugins/quality-check-hook/ .github/workflows/ci.yml .claude-plugin/marketplace.json
git commit -m "feat(quality-check-hook): rename Python package claude_code_hooks → quality_check_hook"
```

Note: Only commit what's staged so far (directory renames + Python changes). CI and marketplace updates come in later tasks.

Actually — at this point only the plugin directory contents have changed. Commit just those:

```bash
git add plugins/quality-check-hook/
git commit -m "feat: rename plugin directory and Python package from claude-code-hooks to quality-check-hook"
```

---

### Task 7: Update generate_schema.py

**Files:**
- Modify: `plugins/quality-check-hook/hook/scripts/generate_schema.py:8,21`

**Step 1: Update import**

Line 8:

```python
# Old:
from claude_code_hooks.config import ClaudeShimConfig
# New:
from quality_check_hook.config import ClaudeShimConfig
```

**Step 2: Update schema $id URL**

Line 21:

```python
# Old:
"https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json"
# New:
"https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json"
```

---

### Task 8: Update schema $id and test data URL

**Files:**
- Modify: `plugins/quality-check-hook/claude-shim.schema.json:65`
- Modify: `plugins/quality-check-hook/hook/tests/test_config.py:87`

**Step 1: Update $id in schema file**

Line 65:

```json
// Old:
"$id": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json"
// New:
"$id": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json"
```

**Step 2: Update test data URL in test_config.py**

Line 87:

```python
# Old:
"$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json",
# New:
"$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
```

**Step 3: Regenerate schema to verify script works**

```bash
cd plugins/quality-check-hook/hook && uv run python scripts/generate_schema.py
```

Expected: "Schema written to ..." — verify the output file matches what we manually edited.

---

### Task 9: Update plugin.json

**Files:**
- Modify: `plugins/quality-check-hook/.claude-plugin/plugin.json`

**Step 1: Update name and bump version**

```json
{
  "name": "quality-check-hook",
  "description": "Config-driven quality checks for edited files — formatting, linting, auto-fix via PostToolUse hooks",
  "version": "0.3.0",
  "author": {
    "name": "elahti"
  },
  "repository": "https://github.com/elahti/claude-shim",
  "license": "MIT",
  "keywords": ["hooks", "linting", "formatting", "quality", "automation"]
}
```

---

### Task 10: Update marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json:8,26-29`

**Step 1: Update the plugin entry and bump versions**

Change the `claude-code-hooks` entry (lines 26-29):

```json
// Old:
{
  "name": "claude-code-hooks",
  "source": "./plugins/claude-code-hooks",
  "description": "Config-driven quality checks for edited files — formatting, linting, auto-fix via PostToolUse hooks",
  "version": "0.2.0"
}
// New:
{
  "name": "quality-check-hook",
  "source": "./plugins/quality-check-hook",
  "description": "Config-driven quality checks for edited files — formatting, linting, auto-fix via PostToolUse hooks",
  "version": "0.3.0"
}
```

**Step 2: Bump marketplace metadata version**

Line 8:

```json
// Old:
"version": "0.10.0"
// New:
"version": "0.11.0"
```

---

### Task 11: Update CI workflow

**Files:**
- Modify: `.github/workflows/ci.yml:39,42,56,70`

**Step 1: Replace all 4 path references (use replace_all)**

```yaml
# Old:
plugins/claude-code-hooks/hook
# New:
plugins/quality-check-hook/hook
```

All 4 occurrences: ruff check (line 39), ruff format (line 42), pyright (line 56), pytest (line 70).

---

### Task 12: Update CLAUDE.md

**Files:**
- Modify: `plugins/quality-check-hook/CLAUDE.md`

**Step 1: Update title**

```markdown
# Old:
# Claude Code Hooks Plugin
# New:
# Quality Check Hook Plugin
```

**Step 2: Update path references**

Line 7:

```markdown
# Old:
The file `claude-shim.schema.json` is generated from the Pydantic models in `hook/src/claude_code_hooks/config.py`.
# New:
The file `claude-shim.schema.json` is generated from the Pydantic models in `hook/src/quality_check_hook/config.py`.
```

Line 12:

```bash
# Old:
cd plugins/claude-code-hooks/hook && uv run python scripts/generate_schema.py
# New:
cd plugins/quality-check-hook/hook && uv run python scripts/generate_schema.py
```

Lines 20-21:

```bash
# Old:
cd plugins/claude-code-hooks/hook
# New:
cd plugins/quality-check-hook/hook
```

---

### Task 13: Update SKILL.md

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md`

**Step 1: Update frontmatter name**

```yaml
# Old:
name: setup
# New:
name: setup-quality-check-hook
```

**Step 2: Update title**

```markdown
# Old:
# Claude Code Hooks — Setup
# New:
# Quality Check Hook — Setup
```

**Step 3: Update uv prerequisite message**

Line 20:

```markdown
# Old:
> The claude-code-hooks plugin requires uv to run. Install it with:
# New:
> The quality-check-hook plugin requires uv to run. Install it with:
```

**Step 4: Update schema URL in example config**

Line 84:

```json
# Old:
"$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/claude-code-hooks/claude-shim.schema.json",
# New:
"$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
```

**Step 5: Update completion message**

Line 98:

```markdown
# Old:
> `.claude-shim.json` has been created. The claude-code-hooks plugin will now automatically run these quality checks whenever Claude edits matching files.
# New:
> `.claude-shim.json` has been created. The quality-check-hook plugin will now automatically run these quality checks whenever Claude edits matching files.
```

---

### Task 14: Run full quality checks and verify no stale references

**Step 1: Run all quality checks**

```bash
cd plugins/quality-check-hook/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright
```

Expected: All pass.

**Step 2: Grep for stale references in live code (excluding docs/plans/)**

```bash
grep -r "claude-code-hooks" --include='*.py' --include='*.json' --include='*.yml' --include='*.md' . | grep -v "docs/plans/"
grep -r "claude_code_hooks" --include='*.py' --include='*.json' --include='*.yml' --include='*.md' . | grep -v "docs/plans/"
```

Expected: No matches. The `docs/plans/` files are historical and should not be updated.

Note: `uv.lock` will contain the new name after `uv lock` in Task 5.

**Step 3: Validate JSON files**

```bash
jq . plugins/quality-check-hook/.claude-plugin/plugin.json > /dev/null && \
jq . plugins/quality-check-hook/hooks/hooks.json > /dev/null && \
jq . plugins/quality-check-hook/claude-shim.schema.json > /dev/null && \
jq . .claude-plugin/marketplace.json > /dev/null && \
echo "All JSON valid"
```

---

### Task 15: Release commit and tag

**Step 1: Stage all changes**

```bash
git add -A
```

**Step 2: Review staged changes**

```bash
git diff --cached --stat
```

Verify the file list matches expectations (~20 files changed, mostly renames + edits).

**Step 3: Commit**

```bash
git commit -m "Release quality-check-hook v0.3.0: rename from claude-code-hooks"
```

**Step 4: Tag**

```bash
git tag quality-check-hook/v0.3.0
```

**Step 5: Push (after user confirmation)**

```bash
git push origin main quality-check-hook/v0.3.0
```

---

## Verification Checklist

After all tasks:

- [ ] `plugins/quality-check-hook/` exists, `plugins/claude-code-hooks/` does not
- [ ] `hook/src/quality_check_hook/` exists, `hook/src/claude_code_hooks/` does not
- [ ] `skills/setup-quality-check-hook/` exists, `skills/setup/` does not
- [ ] All 33 pytest tests pass
- [ ] ruff check, ruff format, pyright all pass
- [ ] Schema regeneration works: `cd plugins/quality-check-hook/hook && uv run python scripts/generate_schema.py`
- [ ] No stale `claude-code-hooks` or `claude_code_hooks` references outside `docs/plans/`
- [ ] All JSON files are valid
- [ ] Plugin version is `0.3.0`, marketplace metadata version is `0.11.0`
