# Remove JSON Schema Feature — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the JSON schema feature (`claude-shim.schema.json`) from the repository — delete the schema file and generator, strip all `$schema` references from configs, docs, skills, and tests.

**Architecture:** Pure deletion/cleanup. No new code, no new dependencies. Each plugin's Pydantic config validation continues to work unchanged — schema was purely for IDE autocompletion.

**Tech Stack:** Markdown, JSON, Python (tests only)

---

### Task 1: Delete schema file and generator script

**Files:**
- Delete: `plugins/quality-check-hook/claude-shim.schema.json`
- Delete: `plugins/quality-check-hook/hook/scripts/generate_schema.py`

**Step 1: Delete the files**

```bash
rm plugins/quality-check-hook/claude-shim.schema.json
rm plugins/quality-check-hook/hook/scripts/generate_schema.py
```

If the `scripts/` directory is now empty, delete it too:
```bash
rmdir plugins/quality-check-hook/hook/scripts/ 2>/dev/null || true
```

**Step 2: Commit**

```bash
git add -u plugins/quality-check-hook/claude-shim.schema.json plugins/quality-check-hook/hook/scripts/generate_schema.py
git commit -m "feat(quality-check-hook): remove JSON schema file and generator"
```

---

### Task 2: Remove `$schema` from `.claude-shim.json`

**Files:**
- Modify: `.claude-shim.json:2`

**Step 1: Remove the `$schema` line**

In `.claude-shim.json`, remove line 2:
```json
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
```

The file should start with:
```json
{
  "quality-checks": {
```

**Step 2: Validate JSON**

```bash
jq . .claude-shim.json > /dev/null
```

Expected: exits 0, no output.

**Step 3: Commit**

```bash
git add .claude-shim.json
git commit -m "chore: remove \$schema reference from .claude-shim.json"
```

---

### Task 3: Update quality-check-hook CLAUDE.md

**Files:**
- Modify: `plugins/quality-check-hook/CLAUDE.md:8,12,22-32`

**Step 1: Remove `generate_schema.py` from architecture list**

Remove this line from the architecture list (line 8):
```
  - `scripts/generate_schema.py` — Schema generator for `claude-shim.schema.json`
```

**Step 2: Remove `claude-shim.schema.json` from architecture list**

Remove this line (line 12):
```
- `claude-shim.schema.json` — JSON Schema for `.claude-shim.json` config files (generated)
```

**Step 3: Remove the entire JSON Schema section**

Remove lines 22-32 (the `### JSON Schema` heading and everything up to the blank line before `### Quality Checks`):

```markdown
### JSON Schema

The file `claude-shim.schema.json` is generated from the Pydantic models in `hook/src/quality_check_hook/config.py`.

**When you modify the config models, regenerate the schema:**

```bash
cd plugins/quality-check-hook/hook && uv run python scripts/generate_schema.py
```

Commit the updated `claude-shim.schema.json` alongside your model changes.
```

**Step 4: Commit**

```bash
git add plugins/quality-check-hook/CLAUDE.md
git commit -m "docs(quality-check-hook): remove JSON schema references from CLAUDE.md"
```

---

### Task 4: Update setup-quality-check-hook SKILL.md

**Files:**
- Modify: `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md:125`

**Step 1: Remove `$schema` from the example config in Step 6**

In the Step 6 example config block (lines 123-135), remove the `$schema` line (line 125):
```json
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
```

The example should become:
```json
{
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

**Step 2: Commit**

```bash
git add plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md
git commit -m "feat(quality-check-hook): remove \$schema from setup skill example config"
```

---

### Task 5: Update README.md

**Files:**
- Modify: `README.md:38`

**Step 1: Remove `$schema` from the example config**

Remove line 38:
```json
  "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
```

The example should start with:
```json
{
  "quality-checks": {
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: remove \$schema from README example config"
```

---

### Task 6: Remove `test_schema_key_ignored` from quality-check-hook tests

**Files:**
- Modify: `plugins/quality-check-hook/hook/tests/test_config.py:85-98`

**Step 1: Remove the test**

Delete the entire `test_schema_key_ignored` method (lines 85-98):

```python
    def test_schema_key_ignored(self, tmp_path: Path) -> None:
        config_data = {
            "$schema": "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json",
            "quality-checks": {
                "include": [{"pattern": "**/*.py", "commands": ["ruff check"]}]
            },
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert len(result.quality_checks.include) == 1
```

**Step 2: Run tests to verify nothing breaks**

```bash
cd plugins/quality-check-hook/hook && uv run pytest -v
```

Expected: all remaining tests pass.

**Step 3: Commit**

```bash
git add plugins/quality-check-hook/hook/tests/test_config.py
git commit -m "test(quality-check-hook): remove test_schema_key_ignored test"
```

---

### Task 7: Remove `$schema` from github-project-tools test data

**Files:**
- Modify: `plugins/github-project-tools/hook/tests/test_config.py:86`

**Step 1: Remove `$schema` from `test_extra_keys_ignored` test data**

In `test_extra_keys_ignored` (line 84-110), remove line 86:
```python
            "$schema": "https://example.com/schema.json",
```

Keep the test itself — it still tests that `quality-checks` and other extra keys at the top level are ignored by the github-project-tools config loader. The test data should become:

```python
        config_data: dict[str, object] = {
            "quality-checks": {"include": []},
            "github-project-tools": {
```

**Step 2: Run tests to verify nothing breaks**

```bash
cd plugins/github-project-tools/hook && uv run pytest -v
```

Expected: all tests pass.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/hook/tests/test_config.py
git commit -m "test(github-project-tools): remove \$schema from test_extra_keys_ignored test data"
```

---

### Task 8: Remove `$schema` from historical planning doc

**Files:**
- Modify: `docs/plans/2026-02-28-configurable-github-project-skills.md:211`

**Step 1: Remove `$schema` from sample config**

In the `test_extra_keys_ignored` code block (around line 211), remove:
```python
            "$schema": "https://example.com/schema.json",
```

**Step 2: Commit**

```bash
git add docs/plans/2026-02-28-configurable-github-project-skills.md
git commit -m "docs: remove \$schema from historical planning doc sample"
```

---

### Task 9: Final verification

**Step 1: Search for any remaining schema references**

```bash
grep -r '\$schema' --include='*.json' --include='*.md' --include='*.py' . | grep -v renovate.json | grep -v node_modules
```

Expected: no output (only `renovate.json` should have `$schema`, and it's excluded).

**Step 2: Run all tests**

```bash
cd plugins/quality-check-hook/hook && uv run pytest -v
cd ../../../github-project-tools/hook && uv run pytest -v
```

Expected: all tests pass in both plugins.

**Step 3: Verify schema files are gone**

```bash
ls plugins/quality-check-hook/claude-shim.schema.json 2>&1
ls plugins/quality-check-hook/hook/scripts/generate_schema.py 2>&1
```

Expected: both return "No such file or directory".
