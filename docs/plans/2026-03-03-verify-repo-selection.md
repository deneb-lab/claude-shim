# Verify Which Repo to Use — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Store the target repository in `.claude-shim.json` so all github-project-tools skills use it consistently, with a migration prompt for existing configs missing the field.

**Architecture:** Add optional `repo` field to the pydantic config model. The setup skill writes it during initial config. The shared `setup.md` prompt checks for it after `read-config` and prompts if missing. URL-based overrides from `parse-issue-arg.md` take precedence.

**Tech Stack:** Python (pydantic), Markdown (SKILL.md, prompt files), pytest

---

### Task 1: Add `repo` field to config model

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/config.py:30`
- Test: `plugins/github-project-tools/hook/tests/test_config.py`

**Step 1: Write the failing test**

Add two tests to `test_config.py` — one for config with repo, one for config without repo (backward compat):

```python
def test_config_with_repo(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "repo": "owner/my-repo",
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {
                        "name": "In Progress",
                        "option-id": "PVTO_2",
                    },
                    "done": {"name": "Done", "option-id": "PVTO_3"},
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(tmp_path)

    assert result is not None
    assert result.repo == "owner/my-repo"

def test_config_without_repo_returns_none_repo(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {
                        "name": "In Progress",
                        "option-id": "PVTO_2",
                    },
                    "done": {"name": "Done", "option-id": "PVTO_3"},
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(tmp_path)

    assert result is not None
    assert result.repo is None
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py::TestGitHubProjectToolsConfig::test_config_with_repo tests/test_config.py::TestGitHubProjectToolsConfig::test_config_without_repo_returns_none_repo -v`
Expected: FAIL — `test_config_with_repo` fails because `GitHubProjectToolsConfig` has no `repo` attribute

**Step 3: Add `repo` field to the model**

In `config.py`, add `repo` to `GitHubProjectToolsConfig`:

```python
class GitHubProjectToolsConfig(BaseModel):
    repo: str | None = None
    project: str
    fields: ProjectFields
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py -v`
Expected: ALL PASS

**Step 5: Run full quality checks**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All clean

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/config.py plugins/github-project-tools/hook/tests/test_config.py
git commit -m "feat(github-project-tools): add optional repo field to config model"
```

---

### Task 2: Include `repo` in `read-config` output

**Files:**
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

The `read-config` subcommand already serializes the full model via `config.model_dump_json(by_alias=True)`, so the `repo` field will appear automatically when present. We just need to verify it in tests.

**Step 1: Write the test**

Add a test to the `TestReadConfig` class in `test_cli.py`:

```python
def test_outputs_repo_when_present(
    self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "repo": "owner/my-repo",
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {
                        "name": "In Progress",
                        "option-id": "PVTO_2",
                    },
                    "done": {"name": "Done", "option-id": "PVTO_3"},
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    exit_code = main(["read-config"], cwd=tmp_path)

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["repo"] == "owner/my-repo"

def test_outputs_null_repo_when_absent(
    self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_config(tmp_path)

    exit_code = main(["read-config"], cwd=tmp_path)

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["repo"] is None
```

**Step 2: Run tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestReadConfig -v`
Expected: ALL PASS (the model serialization already handles this from Task 1)

**Step 3: Commit**

```bash
git add plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "test(github-project-tools): add read-config tests for repo field"
```

---

### Task 3: Remove dead `detect_repo` call in `repo_only_cmds`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:644-656`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Verify the dead code**

In `cli.py`, the `repo_only_cmds` section (around line 644) calls `detect_repo(repo)` but the result `resolved_repo` is never passed to `cmd_get_parent`, `cmd_count_open_sub_issues`, or `cmd_set_parent` — they only use GraphQL node IDs.

**Step 2: Remove the dead code**

Change the `repo_only_cmds` section from:

```python
    repo_only_cmds = {
        "get-parent",
        "count-open-sub-issues",
        "set-parent",
    }
    if subcmd in repo_only_cmds:
        resolved_repo = detect_repo(repo)

        if subcmd == "get-parent":
```

To:

```python
    repo_only_cmds = {
        "get-parent",
        "count-open-sub-issues",
        "set-parent",
    }
    if subcmd in repo_only_cmds:
        if subcmd == "get-parent":
```

**Step 3: Run all tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: ALL PASS

**Step 4: Run quality checks**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All clean

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py
git commit -m "fix(github-project-tools): remove dead detect_repo call in repo_only_cmds"
```

---

### Task 4: Add `repo` to setup skill config template

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:120-139`

**Step 1: Update the config JSON template in Step 6**

In SKILL.md, the Step 6 config template currently shows:

```json
{
  "github-project-tools": {
    "project": "<PROJECT_URL>",
    "fields": {
```

Change it to:

```json
{
  "github-project-tools": {
    "repo": "<REPO>",
    "project": "<PROJECT_URL>",
    "fields": {
```

**Step 2: Verify no other places in the skill need updating**

Read the full SKILL.md. Step 2 already detects the repo and saves it as `REPO`. Step 6 now includes it in the config. No other changes needed.

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): add repo field to setup skill config template"
```

---

### Task 5: Update shared `setup.md` prompt with repo check

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/setup.md`
- Modify: `plugins/github-project-tools/skills/start-implementation/prompts/setup.md`
- Modify: `plugins/github-project-tools/skills/end-implementation/prompts/setup.md`

All three files must be identical after this change. Refer to: repo root CLAUDE.md shared prompt sync rules.

**Step 1: Write the updated `setup.md` content**

Replace the full content of all three `setup.md` files with:

```markdown
The CLI auto-detects the current repository from the git remote. When `REPO_OVERRIDE` is set, pass `--repo $REPO_OVERRIDE` before the subcommand in every CLI invocation to override auto-detection.

1. Read the project config:
   ```bash
   <cli> read-config
   ```

   - **If the command succeeds** (exit code 0), it outputs JSON. Extract and save:
     - `START_FIELD` from `.fields.start-date`
     - `END_FIELD` from `.fields.end-date`
     - The `set-status` subcommand accepts `todo`, `in-progress`, and `done` directly — no manual mapping needed.
     - Note that **a project is available** — proceed with project operations in later phases.

   - **If the command fails** (exit code 1), no config is available. Tell the user:
     "No github-project-tools configuration found. Running setup."
     Then invoke the `github-project-tools:setup-github-project-tools` skill via the Skill tool.
     After setup completes, re-run `<cli> read-config` and extract the values above.

2. Check the `repo` field in the config output:

   - **If `repo` is present** (not null): Use it as `REPO_OVERRIDE` for all subsequent CLI commands. Pass `--repo $REPO_OVERRIDE` before the subcommand in every invocation.

   - **If `repo` is null or missing:**
     1. Detect the current repository:
        ```bash
        <cli> repo-detect
        ```
     2. Use AskUserQuestion to ask: "No repository configured in `.claude-shim.json`. Detected: `<detected-repo>`. Use this repository for issue operations?"
        - **Yes, use this repository** — save as `REPO_OVERRIDE`.
        - **No, let me specify** — ask the user for the correct `owner/repo` value. Save as `REPO_OVERRIDE`.
     3. Read `.claude-shim.json`, add the `repo` field to the `github-project-tools` key with the confirmed value, preserve all other keys, and write back using the Write tool.
     4. Use AskUserQuestion to ask: "Updated `.claude-shim.json` with repo. Commit the change?"
        - If yes: commit the file.
        - If no: leave uncommitted.
     5. Use the confirmed repo as `REPO_OVERRIDE` going forward.

   **Never continue to the next phase without `REPO_OVERRIDE` set.**
```

**Step 2: Write the updated content to all three files**

Write the identical content to:
1. `plugins/github-project-tools/skills/add-issue/prompts/setup.md`
2. `plugins/github-project-tools/skills/start-implementation/prompts/setup.md`
3. `plugins/github-project-tools/skills/end-implementation/prompts/setup.md`

**Step 3: Verify all three copies are identical**

Run: `diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/start-implementation/prompts/setup.md && diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/end-implementation/prompts/setup.md && echo "All identical"`
Expected: "All identical"

**Step 4: Commit**

```bash
git add plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/start-implementation/prompts/setup.md plugins/github-project-tools/skills/end-implementation/prompts/setup.md
git commit -m "feat(github-project-tools): add repo check to shared setup.md prompt"
```

---

### Task 6: Update `.claude-shim.json` in this repo

**Files:**
- Modify: `.claude-shim.json`

**Step 1: Add `repo` field to the existing config**

The current `.claude-shim.json` has a `github-project-tools` key without `repo`. Add it:

```json
"github-project-tools": {
    "repo": "elahti/claude-shim",
    "project": "https://github.com/users/elahti/projects/1",
    ...
}
```

**Step 2: Commit**

```bash
git add .claude-shim.json
git commit -m "chore: add repo field to github-project-tools config"
```

---

### Task 7: Final verification

**Step 1: Run all tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`
Expected: ALL PASS

**Step 2: Run quality checks**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All clean

**Step 3: Verify shared prompt sync**

Run: `diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/start-implementation/prompts/setup.md && diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/end-implementation/prompts/setup.md && echo "All identical"`
Expected: "All identical"

**Step 4: Review the full diff**

Run: `git diff main...HEAD`
Verify all changes are correct and complete.
