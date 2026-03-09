# Fix set-date stale field IDs — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Detect stale date field IDs before the GraphQL mutation and give clear guidance to re-run setup.

**Architecture:** Add a `DateField` Pydantic model with `id` and `type`. Validate field type in `cmd_set_date` before the mutation. Add a hint on any `set-date` failure. Update setup skill to write the new format. Update shared `setup.md` prompts to extract `.id` from the object.

**Tech Stack:** Python (Pydantic), shell scripts, SKILL.md prompts

---

### Task 1: Add DateField model and backward-compat validator

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/config.py:58-62`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write failing tests for new config model**

Add a new test class after the existing `TestReadConfig` class. Add tests for: new format parses correctly, old string format still works, `read-config` outputs the new format.

In `plugins/github-project-tools/hook/tests/test_cli.py`, add a helper that creates config with the new format:

```python
def make_config_new_date_format(tmp_path: Path) -> dict[str, object]:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": {"id": "PVTF_start", "type": "DATE"},
                "end-date": {"id": "PVTF_end", "type": "DATE"},
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
    return config_data
```

Add test cases inside the existing `TestReadConfig` class:

```python
def test_new_date_format_parses(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    make_config_new_date_format(tmp_path)
    exit_code = main(["read-config"], cwd=tmp_path)
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["fields"]["start-date"] == {"id": "PVTF_start", "type": "DATE"}
    assert out["fields"]["end-date"] == {"id": "PVTF_end", "type": "DATE"}

def test_old_string_format_normalizes(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    make_config(tmp_path)
    exit_code = main(["read-config"], cwd=tmp_path)
    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["fields"]["start-date"] == {"id": "PVTF_start", "type": None}
    assert out["fields"]["end-date"] == {"id": "PVTF_end", "type": None}
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestReadConfig::test_new_date_format_parses tests/test_cli.py::TestReadConfig::test_old_string_format_normalizes -v`
Expected: FAIL — new format rejected by current `str` type, old format doesn't produce objects.

**Step 3: Implement DateField model and validator**

In `plugins/github-project-tools/hook/src/github_project_tools/config.py`:

Add a new `DateField` model before `ProjectFields`:

```python
class DateField(BaseModel):
    id: str
    type: str | None = None
```

Change `ProjectFields` date fields from `str` to `DateField`:

```python
class ProjectFields(BaseModel):
    start_date: DateField = Field(alias="start-date")
    end_date: DateField = Field(alias="end-date")
    status: StatusField
    issue_types: list[IssueType] | None = Field(None, alias="issue-types")
```

Add a `model_validator(mode="before")` to `ProjectFields` that normalizes plain strings:

```python
@model_validator(mode="before")
@classmethod
def _normalize_date_fields(cls, data: dict[str, object]) -> dict[str, object]:
    for key in ("start-date", "end-date"):
        val = data.get(key)
        if isinstance(val, str):
            data[key] = {"id": val, "type": None}
    return data
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestReadConfig -v`
Expected: ALL TestReadConfig tests PASS (including existing ones — old format still works).

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/config.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add DateField model with backward-compat validator"
```

---

### Task 2: Update cmd_set_date with pre-validation and failure hint

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:675-700`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write failing tests for field type validation**

Add these tests to the existing `TestSetDate` class:

```python
def test_rejects_non_date_field_type(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": {"id": "PVTF_start", "type": "NUMBER"},
                "end-date": {"id": "PVTF_end", "type": "DATE"},
                "status": {
                    "id": "PVTF_status",
                    "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    "in-progress": {"name": "In Progress", "option-id": "PVTO_2"},
                    "done": {"name": "Done", "option-id": "PVTO_3"},
                },
            },
        }
    }
    (tmp_path / ".claude-shim.json").write_text(json.dumps(config_data))
    exit_code = main(
        ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
        cwd=tmp_path,
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "NUMBER" in err
    assert "expected DATE" in err
    assert "setup-github-project-tools" in err

def test_skips_validation_when_type_is_null(self, tmp_path: Path) -> None:
    make_config(tmp_path)  # old format — type will be None
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
            ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
            cwd=tmp_path,
        )
    assert exit_code == 0

def test_failure_includes_hint(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    make_config(tmp_path)
    with patch("github_project_tools.cli.run_gh") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="PVT_proj\n", stderr=""
            ),
            subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="Did not receive a number value"
            ),
        ]
        exit_code = main(
            ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
            cwd=tmp_path,
        )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "setup-github-project-tools" in err
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetDate::test_rejects_non_date_field_type tests/test_cli.py::TestSetDate::test_skips_validation_when_type_is_null tests/test_cli.py::TestSetDate::test_failure_includes_hint -v`
Expected: FAIL

**Step 3: Implement pre-validation and failure hint**

In `plugins/github-project-tools/hook/src/github_project_tools/cli.py`, modify `cmd_set_date`:

```python
def cmd_set_date(
    config: GitHubProjectToolsConfig,
    item_id: str,
    field_id: str,
    date_value: str | None = None,
) -> int:
    # Pre-validate field type if metadata is available
    for date_field in (config.fields.start_date, config.fields.end_date):
        if date_field.id == field_id and date_field.type is not None:
            if date_field.type != "DATE":
                print(
                    f"set-date: field {field_id} has type {date_field.type}, expected DATE. "
                    "Re-run github-project-tools:setup-github-project-tools to refresh field IDs.",
                    file=sys.stderr,
                )
                return 1
            break

    project_id = get_project_id(config)
    date = date_value or datetime.now(UTC).date().isoformat()
    result = graphql(
        """
        mutation($project: ID!, $item: ID!, $field: ID!, $date: Date!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $project, itemId: $item,
            fieldId: $field, value: {date: $date}
          }) { projectV2Item { id } }
        }""",
        {
            "project": project_id,
            "item": item_id,
            "field": field_id,
            "date": date,
        },
    )
    if (rc := check_result(result, "set-date")) is not None:
        print(
            "Hint: if field IDs are stale, re-run "
            "github-project-tools:setup-github-project-tools to refresh them.",
            file=sys.stderr,
        )
        return rc
    return 0
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetDate -v`
Expected: ALL TestSetDate tests PASS.

**Step 5: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): validate date field type before mutation and add failure hint"
```

---

### Task 3: Fix existing tests that use old config format with set-date

**Files:**
- Modify: `plugins/github-project-tools/hook/tests/test_cli.py`

The existing `TestSetDate` tests use `make_config` which has old-format string date fields. After Task 1, these will be normalized to `DateField(id=..., type=None)`. The existing tests should still pass because `cmd_set_date` receives `field_id` as a string from CLI args and the config just needs to load.

**Step 1: Run the full test suite**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py -v`
Expected: PASS (if any tests fail due to the config model change, fix them).

**Step 2: If any tests fail, update them**

The most likely breakage is in `TestReadConfig` tests that assert exact JSON output format — `"start-date": "PVTF_start"` will now become `"start-date": {"id": "PVTF_start", "type": null}`.

Update any assertions in existing `TestReadConfig` tests that check the date field values in the JSON output. For example:

```python
# Old assertion:
assert out["fields"]["start-date"] == "PVTF_start"
# New assertion:
assert out["fields"]["start-date"] == {"id": "PVTF_start", "type": None}
```

**Step 3: Run the full test suite again**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py -v`
Expected: ALL tests PASS.

**Step 4: Run linting and type checks**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: PASS

**Step 5: Commit (only if changes were needed)**

```bash
git add plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "fix(github-project-tools): update existing tests for new DateField config format"
```

---

### Task 4: Update shared setup.md prompts

**Files:**
- Modify: `plugins/github-project-tools/skills/add-issue/prompts/setup.md`
- Modify: `plugins/github-project-tools/skills/start-implementing-issue/prompts/setup.md`
- Modify: `plugins/github-project-tools/skills/end-implementing-issue/prompts/setup.md`
- Modify: `plugins/github-project-tools/skills/mass-update-issues/prompts/setup.md`

All four files are identical. The change is the same in each.

**Step 1: Update field extraction instructions**

In each `setup.md`, change lines 8-10 from:

```markdown
   - **If the command succeeds** (exit code 0), it outputs JSON. Extract and save:
     - `START_FIELD` from `.fields.start-date`
     - `END_FIELD` from `.fields.end-date`
```

to:

```markdown
   - **If the command succeeds** (exit code 0), it outputs JSON. Extract and save:
     - `START_FIELD` from `.fields.start-date.id`
     - `END_FIELD` from `.fields.end-date.id`
```

**Step 2: Verify all four copies are identical**

Run: `diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/start-implementing-issue/prompts/setup.md && diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/end-implementing-issue/prompts/setup.md && diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/mass-update-issues/prompts/setup.md && echo "All identical"`

Expected: "All identical"

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/*/prompts/setup.md
git commit -m "feat(github-project-tools): update setup.md prompts to extract date field .id"
```

---

### Task 5: Update setup skill to write new date field format

**Files:**
- Modify: `plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md:144-168`

**Step 1: Update the config template in Step 6**

In the setup skill's SKILL.md, change the config JSON template from:

```json
"start-date": "<START_FIELD_ID>",
"end-date": "<END_FIELD_ID>",
```

to:

```json
"start-date": {"id": "<START_FIELD_ID>", "type": "DATE"},
"end-date": {"id": "<END_FIELD_ID>", "type": "DATE"},
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/setup-github-project-tools/SKILL.md
git commit -m "feat(github-project-tools): setup skill writes date field type metadata"
```

---

### Task 6: Final verification

**Step 1: Run full test suite**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/ -v`
Expected: ALL tests PASS.

**Step 2: Run linting and type checks**

Run: `cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: PASS.

**Step 3: Verify shared prompt sync**

Run: `diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/start-implementing-issue/prompts/setup.md && diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/end-implementing-issue/prompts/setup.md && diff plugins/github-project-tools/skills/add-issue/prompts/setup.md plugins/github-project-tools/skills/mass-update-issues/prompts/setup.md && echo "All identical"`
Expected: "All identical"

**Step 4: Review all changes**

Run: `git diff main...HEAD --stat` and `git log main...HEAD --oneline`
Expected: Changes only in config.py, cli.py, test_cli.py, setup.md (x4), SKILL.md (setup), and plan docs.
