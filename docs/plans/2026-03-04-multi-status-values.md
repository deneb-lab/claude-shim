# Multi-Status Values Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Support multiple status values per logical state (todo, in-progress, done) in `.claude-shim.json`, with backwards compatibility for existing single-object configs.

**Architecture:** Add a `default` field to `StatusMapping`, change `StatusField` to accept union types (`StatusMapping | list[StatusMapping]`), add a model validator and `get_default()` helper. Update `cmd_set_status` to use the helper. Update the setup skill to always write list format and offer multi-select.

**Tech Stack:** Python 3.x, Pydantic v2, pytest, SKILL.md (Markdown)

---

### Task 1: Add `default` field to `StatusMapping`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/config.py:12-14`
- Test: `plugins/github-project-tools/hook/tests/test_config.py`

**Step 1: Write the failing test**

Add to `TestGitHubProjectToolsConfig` in `test_config.py`:

```python
def test_status_mapping_default_field(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1", "default": True},
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
    assert result.fields.status.todo.default is True
    assert result.fields.status.in_progress.default is False
    assert result.fields.status.done.default is False
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py::TestGitHubProjectToolsConfig::test_status_mapping_default_field -v`

Expected: FAIL — `StatusMapping` has no `default` attribute.

**Step 3: Write minimal implementation**

In `config.py`, add `default` to `StatusMapping`:

```python
class StatusMapping(BaseModel):
    name: str
    option_id: str = Field(alias="option-id")
    default: bool = False
```

**Step 4: Run test to verify it passes**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py::TestGitHubProjectToolsConfig::test_status_mapping_default_field -v`

Expected: PASS

**Step 5: Run full test suite to check nothing broke**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`

Expected: All existing tests still PASS (backwards compat — `default` has a default value of `False`).

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/config.py plugins/github-project-tools/hook/tests/test_config.py
git commit -m "feat(github-project-tools): add default field to StatusMapping"
```

---

### Task 2: Update `StatusField` to accept union types

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/config.py:17-21`
- Test: `plugins/github-project-tools/hook/tests/test_config.py`

**Step 1: Write the failing tests**

Add to `TestGitHubProjectToolsConfig` in `test_config.py`:

```python
def test_status_as_list_with_single_item(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": [{"name": "Todo", "option-id": "PVTO_1", "default": True}],
                    "in-progress": [
                        {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                            "default": True,
                        }
                    ],
                    "done": [{"name": "Done", "option-id": "PVTO_3", "default": True}],
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(tmp_path)

    assert result is not None
    assert isinstance(result.fields.status.todo, list)
    assert len(result.fields.status.todo) == 1
    assert result.fields.status.todo[0].name == "Todo"
    assert result.fields.status.todo[0].option_id == "PVTO_1"
    assert result.fields.status.todo[0].default is True

def test_status_as_list_with_multiple_items(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {"name": "In Progress", "option-id": "PVTO_2"},
                    "done": [
                        {
                            "name": "Done",
                            "option-id": "PVTO_3",
                            "default": True,
                        },
                        {
                            "name": "Arkisto",
                            "option-id": "PVTO_4",
                        },
                    ],
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    result = load_config(tmp_path)

    assert result is not None
    assert isinstance(result.fields.status.done, list)
    assert len(result.fields.status.done) == 2
    assert result.fields.status.done[0].name == "Done"
    assert result.fields.status.done[0].default is True
    assert result.fields.status.done[1].name == "Arkisto"
    assert result.fields.status.done[1].default is False

def test_status_list_without_default_raises(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {"name": "In Progress", "option-id": "PVTO_2"},
                    "done": [
                        {"name": "Done", "option-id": "PVTO_3"},
                        {"name": "Arkisto", "option-id": "PVTO_4"},
                    ],
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    with pytest.raises(ValueError):
        load_config(tmp_path)

def test_status_list_with_multiple_defaults_raises(self, tmp_path: Path) -> None:
    config_data = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {"name": "In Progress", "option-id": "PVTO_2"},
                    "done": [
                        {
                            "name": "Done",
                            "option-id": "PVTO_3",
                            "default": True,
                        },
                        {
                            "name": "Arkisto",
                            "option-id": "PVTO_4",
                            "default": True,
                        },
                    ],
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    with pytest.raises(ValueError):
        load_config(tmp_path)
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py -k "list" -v`

Expected: FAIL — `StatusField` does not accept list types.

**Step 3: Write the implementation**

In `config.py`, update `StatusField`:

```python
from pydantic import BaseModel, Field, ValidationError, model_validator


class StatusField(BaseModel):
    id: str
    todo: StatusMapping | list[StatusMapping]
    in_progress: StatusMapping | list[StatusMapping] = Field(alias="in-progress")
    done: StatusMapping | list[StatusMapping]

    @model_validator(mode="after")
    def _check_list_defaults(self) -> StatusField:
        for key in ("todo", "in_progress", "done"):
            value = getattr(self, key)
            if isinstance(value, list):
                defaults = [m for m in value if m.default]
                label = key.replace("_", "-")
                if len(defaults) != 1:
                    msg = (
                        f"Status list for '{label}' must have exactly one default, "
                        f"found {len(defaults)}"
                    )
                    raise ValueError(msg)
        return self

    def get_default(self, key: str) -> StatusMapping:
        """Return the default StatusMapping for a logical state.

        Args:
            key: One of "todo", "in-progress", "done".

        Returns:
            The default StatusMapping for the given state.

        Raises:
            ValueError: If the key is unknown.
        """
        attr = key.replace("-", "_")
        value = getattr(self, attr, None)
        if value is None:
            msg = f"Unknown status key: '{key}'"
            raise ValueError(msg)
        if isinstance(value, StatusMapping):
            return value
        defaults = [m for m in value if m.default]
        return defaults[0]
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py -v`

Expected: All tests PASS, including the new list-format tests.

**Step 5: Run lint and typecheck**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`

Expected: All pass. If pyright complains about the union type or `model_validator` import, fix accordingly.

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/config.py plugins/github-project-tools/hook/tests/test_config.py
git commit -m "feat(github-project-tools): support list-type status mappings in StatusField"
```

---

### Task 3: Add `get_default()` unit tests

**Files:**
- Test: `plugins/github-project-tools/hook/tests/test_config.py`

**Step 1: Write tests for `get_default()`**

Add a new test class to `test_config.py`:

```python
from github_project_tools.config import StatusField, StatusMapping


class TestStatusFieldGetDefault:
    def test_get_default_single_object(self) -> None:
        field = StatusField.model_validate({
            "id": "F1",
            "todo": {"name": "Todo", "option-id": "O1"},
            "in-progress": {"name": "In Progress", "option-id": "O2"},
            "done": {"name": "Done", "option-id": "O3"},
        })
        result = field.get_default("todo")
        assert result.option_id == "O1"

    def test_get_default_list(self) -> None:
        field = StatusField.model_validate({
            "id": "F1",
            "todo": {"name": "Todo", "option-id": "O1"},
            "in-progress": {"name": "In Progress", "option-id": "O2"},
            "done": [
                {"name": "Done", "option-id": "O3", "default": True},
                {"name": "Arkisto", "option-id": "O4"},
            ],
        })
        result = field.get_default("done")
        assert result.option_id == "O3"
        assert result.name == "Done"

    def test_get_default_in_progress_with_hyphen(self) -> None:
        field = StatusField.model_validate({
            "id": "F1",
            "todo": {"name": "Todo", "option-id": "O1"},
            "in-progress": [
                {"name": "In Progress", "option-id": "O2", "default": True},
                {"name": "Active", "option-id": "O5"},
            ],
            "done": {"name": "Done", "option-id": "O3"},
        })
        result = field.get_default("in-progress")
        assert result.option_id == "O2"

    def test_get_default_unknown_key_raises(self) -> None:
        field = StatusField.model_validate({
            "id": "F1",
            "todo": {"name": "Todo", "option-id": "O1"},
            "in-progress": {"name": "In Progress", "option-id": "O2"},
            "done": {"name": "Done", "option-id": "O3"},
        })
        with pytest.raises(ValueError, match="Unknown status key"):
            field.get_default("invalid")
```

**Step 2: Run tests**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_config.py::TestStatusFieldGetDefault -v`

Expected: All PASS (implementation was written in Task 2).

**Step 3: Commit**

```bash
git add plugins/github-project-tools/hook/tests/test_config.py
git commit -m "test(github-project-tools): add get_default() unit tests"
```

---

### Task 4: Update `cmd_set_status` to use `get_default()`

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:451-487`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing test**

Add to `TestSetStatus` in `test_cli.py`:

```python
def test_uses_default_from_list_config(self, tmp_path: Path) -> None:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": [
                        {"name": "Todo", "option-id": "PVTO_1", "default": True}
                    ],
                    "in-progress": [
                        {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                            "default": True,
                        }
                    ],
                    "done": [
                        {
                            "name": "Done",
                            "option-id": "PVTO_3",
                            "default": True,
                        },
                        {"name": "Arkisto", "option-id": "PVTO_4"},
                    ],
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    with patch("github_project_tools.cli.run_gh") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="PVT_proj\n", stderr=""
            ),
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout='{"data":{}}', stderr=""
            ),
        ]
        exit_code = main(
            ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
            cwd=tmp_path,
        )
    assert exit_code == 0
    # Should use PVTO_3 (the default), not PVTO_4
    graphql_call = mock_run.call_args_list[1]
    call_str = " ".join(graphql_call[0][0])
    assert "PVTO_3" in call_str
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetStatus::test_uses_default_from_list_config -v`

Expected: FAIL — `cmd_set_status` accesses `.todo.option_id` directly, which fails on a list.

**Step 3: Write the implementation**

Replace `cmd_set_status` in `cli.py`:

```python
def cmd_set_status(
    config: GitHubProjectToolsConfig,
    item_id: str,
    status_key: str,
) -> int:
    valid_keys = ("todo", "in-progress", "done")
    if status_key not in valid_keys:
        print(
            f"set-status: unknown status '{status_key}' (valid: {', '.join(valid_keys)})",
            file=sys.stderr,
        )
        return 1

    mapping = config.fields.status.get_default(status_key)
    option_id = mapping.option_id

    project_id = get_project_id(config)
    field_id = config.fields.status.id
    graphql(
        """
        mutation($project: ID!, $item: ID!, $field: ID!, $value: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $project, itemId: $item,
            fieldId: $field, value: {singleSelectOptionId: $value}
          }) { projectV2Item { id } }
        }""",
        {
            "project": project_id,
            "item": item_id,
            "field": field_id,
            "value": option_id,
        },
    )
    return 0
```

**Step 4: Run all tests to verify everything passes**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`

Expected: All tests PASS — both old single-object config tests and new list config test.

**Step 5: Run lint and typecheck**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`

Expected: All pass.

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): update cmd_set_status to use get_default()"
```

---

### Task 5: Update `read-config` serialization test

**Files:**
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

The `read-config` command uses `model_dump_json(by_alias=True)`. Verify it correctly serializes list-format status fields.

**Step 1: Write the test**

Add to `TestReadConfig` in `test_cli.py`:

```python
def test_outputs_list_status_format(
    self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": "PVTF_start",
                "end-date": "PVTF_end",
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {"name": "In Progress", "option-id": "PVTO_2"},
                    "done": [
                        {
                            "name": "Done",
                            "option-id": "PVTO_3",
                            "default": True,
                        },
                        {"name": "Arkisto", "option-id": "PVTO_4"},
                    ],
                },
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))

    exit_code = main(["read-config"], cwd=tmp_path)

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    # Single object stays as object
    assert isinstance(output["fields"]["status"]["todo"], dict)
    # List stays as list
    assert isinstance(output["fields"]["status"]["done"], list)
    assert len(output["fields"]["status"]["done"]) == 2
    assert output["fields"]["status"]["done"][0]["option-id"] == "PVTO_3"
    assert output["fields"]["status"]["done"][0]["default"] is True
    assert output["fields"]["status"]["done"][1]["option-id"] == "PVTO_4"
    assert output["fields"]["status"]["done"][1]["default"] is False
```

**Step 2: Run test**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestReadConfig::test_outputs_list_status_format -v`

Expected: PASS (Pydantic handles union serialization automatically).

**Step 3: Commit**

```bash
git add plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "test(github-project-tools): add read-config serialization test for list status"
```

---

### Task 6: Update setup skill to detect and write multi-status format

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:89-139`

**Step 1: Read the current skill**

Read `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md` to understand the exact section to modify.

**Step 2: Update Step 5 (Detect Status Mappings)**

Replace the current Step 5 content (lines 89-118) with the multi-select workflow. The new Step 5 should read:

```markdown
## Step 5: Detect Status Mappings

The plugin automatically updates issue status as you work — it needs to know which of your project's status options correspond to three workflow stages:

- **New issues** — set when creating an issue or resetting one that was started but not completed
- **Started work** — set when you begin implementing an issue
- **Finished work** — set when you close an issue after implementation is complete

Using the status field's `.options` array from Step 4, auto-match option names to these stages:

| Stage | Try matching (case-insensitive) |
|-------|-------------------------------|
| New issues | "Todo", "To Do", "To do", "Backlog", "New" |
| Started work | "In Progress", "In progress", "Working", "Active", "Doing" |
| Finished work | "Done", "Complete", "Completed", "Shipped", "Closed" |

For each stage:
1. Auto-match candidates from the options list using the name patterns above.
2. Present **all** status options to the user with AskUserQuestion using `multiSelect: true`. Pre-select any auto-matched options by listing them first and marking them as "(Recommended)" in the label.
3. The user selects which options map to this stage (one or more).
4. If multiple options were selected, ask the user which one should be the **default** (the status value used when the skill sets status for this stage).
5. If only one option was selected, it is automatically the default.

Present the proposed mapping for confirmation:
```
Status mappings:
  New issues    → "Todo" (default)
  Started work  → "In Progress" (default)
  Finished work → "Done" (default), "Arkisto"
```

Ask: "Does this look right?"
```

**Step 3: Update Step 6 (Write Config)**

Replace the config template in Step 6 (lines 120-139) to always use list format:

```markdown
## Step 6: Write Config

Build the configuration object. **Always write status mappings as lists**, even when a stage has only one option:

```json
{
  "github-project-tools": {
    "repo": "<REPO>",
    "project": "<PROJECT_URL>",
    "fields": {
      "start-date": "<START_FIELD_ID>",
      "end-date": "<END_FIELD_ID>",
      "status": {
        "id": "<STATUS_FIELD_ID>",
        "todo": [{ "name": "<name>", "option-id": "<id>", "default": true }],
        "in-progress": [{ "name": "<name>", "option-id": "<id>", "default": true }],
        "done": [
          { "name": "<name>", "option-id": "<id>", "default": true },
          { "name": "<name2>", "option-id": "<id2>" }
        ]
      }
    }
  }
}
```

Non-default items in the list omit the `"default"` key (it defaults to `false`).
```

**Step 4: Verify the edits are correct**

Read the modified file end-to-end to confirm the changes are consistent and nothing was accidentally broken.

**Step 5: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): update setup skill for multi-status detection"
```

---

### Task 7: Final verification

**Step 1: Run the full test suite**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v`

Expected: All tests PASS.

**Step 2: Run lint and typecheck**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`

Expected: All pass.

**Step 3: Run shellcheck on all scripts**

Run: `shellcheck plugins/github-project-tools/scripts/*.sh`

Expected: No errors (scripts weren't modified, but verify CI will pass).

**Step 4: Verify JSON validation**

Run: `python -m json.tool .claude-shim.json > /dev/null`

Expected: Valid JSON.

**Step 5: Review all changes**

Run: `git diff main --stat` and `git log main..HEAD --oneline` to review the full changeset.

**Step 6: Commit any remaining fixes**

If any issues were found in steps 1-4, fix and commit.
