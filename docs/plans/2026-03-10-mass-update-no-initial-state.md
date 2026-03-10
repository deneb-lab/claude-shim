# Mass-Update: Remove Initial State Requirement — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the mass-update skill work regardless of the initial open/closed state of the parent issue and sub-issues.

**Architecture:** Add two new CLI subcommands (`clear-date`, `reopen-issue`), then rewrite the mass-update SKILL.md phases to use deterministic behavior based on logical state instead of user prompts for dates/closing.

**Tech Stack:** Python (cli.py), pytest, SKILL.md (prompt engineering), shell (github-project-tools.sh)

---

### Task 1: Add `reopen-issue` CLI subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:355-399` (near `cmd_issue_close`)
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add a new test class `TestIssueReopen` after the `TestIssueClose` class (after line 847 in test_cli.py):

```python
class TestIssueReopen:
    def test_reopens_closed_issue(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="CLOSED\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr=""
                ),
            ]
            exit_code = main(["--repo", "owner/repo", "reopen-issue", "42"])
        assert exit_code == 0
        reopen_args = mock_run.call_args_list[1][0][0]
        assert "edit" in reopen_args
        assert "--state" in reopen_args
        assert "open" in reopen_args

    def test_skips_reopen_for_open_issue(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="OPEN\n", stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "reopen-issue", "42"])
        assert exit_code == 0
        assert "already open" in capsys.readouterr().err.lower()

    def test_reopen_failure_returns_nonzero(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="CLOSED\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="network error"
                ),
            ]
            exit_code = main(["--repo", "owner/repo", "reopen-issue", "42"])
        assert exit_code == 1
        assert "failed" in capsys.readouterr().err.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueReopen -v`
Expected: FAIL — `reopen-issue` is an unknown subcommand

**Step 3: Write the implementation**

Add `cmd_reopen_issue` function in cli.py after `cmd_issue_close` (after line 399):

```python
def cmd_reopen_issue(repo: str, number: str) -> int:
    state_result = run_gh(
        ["issue", "view", number, "--repo", repo, "--json", "state", "--jq", ".state"]
    )
    state = state_result.stdout.strip()

    if state == "OPEN":
        print(f"Issue #{number} is already open — skipping reopen.", file=sys.stderr)
        return 0

    result = run_gh(["issue", "edit", number, "--repo", repo, "--state", "open"])
    if result.returncode != 0:
        print(f"reopen-issue: failed to reopen #{number}", file=sys.stderr)
        return 1
    return 0
```

Add to `_required_args` dict (around line 868):

```python
"reopen-issue": (1, "Usage: reopen-issue <number>"),
```

Add `"reopen-issue"` to the `issue_cmds` set (around line 910).

Add dispatch in the issue commands block (after `issue-assign` dispatch, around line 936):

```python
if subcmd == "reopen-issue":
    return cmd_reopen_issue(resolved_repo, sub_args[0])
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestIssueReopen -v`
Expected: PASS (3 tests)

**Step 5: Run full test suite + lint**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add reopen-issue CLI subcommand"
```

---

### Task 2: Add `clear-date` CLI subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py:675-717` (near `cmd_set_date`)
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add a new test class `TestClearDate` after the `TestSetDate` class:

```python
class TestClearDate:
    def test_clears_date_field(self, tmp_path: Path) -> None:
        make_config(tmp_path)
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
                ["--repo", "owner/repo", "clear-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTI_item" in call_str
        assert "PVTF_start" in call_str

    def test_uses_clear_mutation(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            main(
                ["--repo", "owner/repo", "clear-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "clearProjectV2ItemFieldValue" in call_str

    def test_rejects_non_date_field_type(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config_data: dict[str, object] = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": {"id": "PVTF_start", "type": "NUMBER"},
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
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config_data))
        exit_code = main(
            ["--repo", "owner/repo", "clear-date", "PVTI_item", "PVTF_start"],
            cwd=tmp_path,
        )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "NUMBER" in err
        assert "expected DATE" in err

    def test_skips_validation_when_type_is_null(self, tmp_path: Path) -> None:
        make_config(tmp_path)
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
                ["--repo", "owner/repo", "clear-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )
        assert exit_code == 0

    def test_graphql_failure_returns_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                    stdout="",
                    stderr="mutation failed",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "clear-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )
        assert exit_code == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestClearDate -v`
Expected: FAIL — `clear-date` is an unknown subcommand

**Step 3: Write the implementation**

Add `cmd_clear_date` function in cli.py after `cmd_set_date` (after line 717):

```python
def cmd_clear_date(
    config: GitHubProjectToolsConfig,
    item_id: str,
    field_id: str,
) -> int:
    # Pre-validate field type if metadata is available
    for date_field in (config.fields.start_date, config.fields.end_date):
        if date_field.id == field_id and date_field.type is not None:
            if date_field.type != "DATE":
                print(
                    f"clear-date: field {field_id} has type {date_field.type}, expected DATE. "
                    "Re-run github-project-tools:setup-github-project-tools to refresh field IDs.",
                    file=sys.stderr,
                )
                return 1
            break

    project_id = get_project_id(config)
    result = graphql(
        """
        mutation($project: ID!, $item: ID!, $field: ID!) {
          clearProjectV2ItemFieldValue(input: {
            projectId: $project, itemId: $item,
            fieldId: $field
          }) { projectV2Item { id } }
        }""",
        {
            "project": project_id,
            "item": item_id,
            "field": field_id,
        },
    )
    if (rc := check_result(result, "clear-date")) is not None:
        return rc
    return 0
```

Add to `_required_args` dict:

```python
"clear-date": (2, "Usage: clear-date <item-id> <field-id>"),
```

Add `"clear-date"` to the `config_cmds` set.

Add dispatch in the config commands block:

```python
if subcmd == "clear-date":
    return cmd_clear_date(config, sub_args[0], sub_args[1])
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestClearDate -v`
Expected: PASS (5 tests)

**Step 5: Run full test suite + lint**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 6: Commit**

```bash
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add clear-date CLI subcommand"
```

---

### Task 3: Update SKILL.md allowed-tools and add `reopen-issue` / `clear-date` to permissions

**Files:**
- Modify: `plugins/github-project-tools/skills/mass-update-issues/SKILL.md:4` (allowed-tools line)

**Step 1: Update the allowed-tools frontmatter**

Add two new tool patterns to the `allowed-tools` line in the SKILL.md frontmatter:

```
Bash(*/github-project-tools/scripts/github-project-tools.sh reopen-issue *)
Bash(*/github-project-tools/scripts/github-project-tools.sh clear-date *)
```

Append these to the existing comma-separated list on line 4.

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/mass-update-issues/SKILL.md
git commit -m "feat(github-project-tools): add reopen-issue and clear-date to mass-update allowed-tools"
```

---

### Task 4: Rewrite SKILL.md phases

**Files:**
- Modify: `plugins/github-project-tools/skills/mass-update-issues/SKILL.md`

**Step 1: Rewrite Phase 2**

Replace Phase 2 step 3 ("Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is closed and stop.") with:

```markdown
3. Save `state` as `PARENT_STATE` (either `OPEN` or `CLOSED`). Do **not** reject closed issues.
```

**Step 2: Rewrite Phase 3**

Replace Phase 3 with the following. Key changes:
- When `LOGICAL_STATE` is `null` (custom status), ask whether sub-issues should also be updated.
- The confirmation prompt adjusts based on the scope rules.

Replace from `## Phase 3: Determine Target Status` through the end of Phase 3 with:

```markdown
## Phase 3: Determine Target Status

**User confirmation is MANDATORY. NEVER skip the prompt, even if a state hint was provided.**

1. Read the config's status field to understand available logical states and their default mappings.

2. **If `STATE_HINT` is set** (todo, in-progress, or done):
   - Look up the default status mapping from config for that logical state.
   - Extract the `name` and `option-id` as the suggested status.
   - Save `STATE_HINT` as `LOGICAL_STATE`.

3. **If `STATE_HINT` is not set:**
   - No auto-detection. `LOGICAL_STATE` is null.

4. **Always prompt the user using AskUserQuestion.** Present options:
   - If a suggestion was auto-detected: "Use `<suggested_name>` (from `<LOGICAL_STATE>` state)" as the first/default option.
   - "Provide a custom status name" as another option.
   - If no suggestion: only show "Provide a custom status name" and list the logical states (todo, in-progress, done) as options too.

5. **If the user provides a custom status name:**
   a. Fetch all available status options:
      ```bash
      <cli> list-status-options
      ```
   b. Match the user-provided name against the returned options (case-insensitive).
   c. If a match is found: save the matching `id` as `OPTION_ID`. Check if this option ID matches any logical state's default in the config. If it does, set `LOGICAL_STATE` to that state. Otherwise, `LOGICAL_STATE` is null.
   d. If no match: show the available status options and ask the user again. Repeat until a valid status is confirmed.

6. **If the user selected the auto-detected suggestion:**
   - Save the option-id from config as `OPTION_ID`.

7. **If `LOGICAL_STATE` is null** (custom status with no logical mapping):
   - Ask the user: "Should sub-issues also be updated to `<status_name>`?"
   - Save the answer as `UPDATE_SUBS` (boolean).

8. Determine the update scope based on `LOGICAL_STATE` and `PARENT_STATE`:

   | Target | Parent OPEN | Parent CLOSED |
   |---|---|---|
   | **done** | Status + end-date + close on parent AND all subs | Status + end-date + close on parent AND all subs |
   | **todo** | Status + clear start & end dates on parent AND all subs | Reopen parent. Status + clear start & end dates on parent only |
   | **in-progress** | Status + start-date (if missing) + clear end-date on parent only | Reopen parent. Status + start-date (if missing) + clear end-date on parent only |
   | **custom (null)** | Status on parent. Subs only if `UPDATE_SUBS` is true | Status on parent. Subs only if `UPDATE_SUBS` is true |

9. Confirm the final choice. Summarize all planned actions:
   ```
   Will update #<number> (and <count> sub-issues):
   - Status: <status_name>
   - Dates: <what will happen with dates, or "no changes">
   - Open/close: <what will happen, or "no changes">
   Proceed?
   ```
   - **Wait for explicit confirmation before continuing.**
```

**Step 3: Remove Phases 4 and 5, rewrite Phase 6 as Phase 4**

Delete Phase 4 (Determine Date Handling) and Phase 5 (Determine Close Handling) entirely.

Replace Phase 6 with:

```markdown
## Phase 4: Execute Updates

**Order: sub-issues first, then parent.**

Determine which issues to update:
- **done**: parent and all sub-issues.
- **todo**: parent and all sub-issues if `PARENT_STATE` was `OPEN`; parent only if `PARENT_STATE` was `CLOSED`.
- **in-progress**: parent only.
- **custom (null)**: parent always; sub-issues only if `UPDATE_SUBS` is true.

For each issue in the update list (sub-issues first, then the parent):

1. **Ensure issue is on the project board:**
   ```bash
   <cli> get-project-item "$ISSUE_NODE_ID"
   ```
   - If the output is **non-empty**: save as `ISSUE_ITEM_ID`.
   - If the output is **empty**: add to project:
     ```bash
     <cli> add-to-project "$ISSUE_NODE_ID"
     ```
     Save the output as `ISSUE_ITEM_ID`.

2. **Set status:**
   ```bash
   <cli> set-status-by-option-id "$ISSUE_ITEM_ID" "$OPTION_ID"
   ```

3. **Date operations** (based on `LOGICAL_STATE`):

   - **done**: Set end date:
     ```bash
     <cli> set-date "$ISSUE_ITEM_ID" "$END_FIELD"
     ```

   - **todo**: Clear start and end dates:
     ```bash
     <cli> clear-date "$ISSUE_ITEM_ID" "$START_FIELD"
     <cli> clear-date "$ISSUE_ITEM_ID" "$END_FIELD"
     ```

   - **in-progress**: Check start date, set if missing. Clear end date:
     ```bash
     <cli> get-start-date "$ISSUE_NODE_ID"
     ```
     If the date is `null`, set it:
     ```bash
     <cli> set-date "$ISSUE_ITEM_ID" "$START_FIELD"
     ```
     Then clear end date:
     ```bash
     <cli> clear-date "$ISSUE_ITEM_ID" "$END_FIELD"
     ```

   - **custom (null)**: No date operations.

4. **Open/Close** (based on `LOGICAL_STATE`):

   - **done**: Close the issue:
     ```bash
     <cli> issue-close <issue_number>
     ```

   - **todo** or **in-progress**: Reopen **only the parent** (if `PARENT_STATE` was `CLOSED` and this is the parent issue):
     ```bash
     <cli> reopen-issue <parent_number>
     ```
     Do **not** reopen sub-issues.

   - **custom (null)**: No open/close operations.

5. **Report progress** after each issue:
   ```
   Updated #<number> (<title>): status → <status_name>
   ```

After all updates complete, display a summary:
```
Mass update complete:
- Status: <status_name>
- Issues updated: <count>
- Dates set/cleared: <count> (or "skipped")
- Issues closed: <count> (or "skipped")
- Issues reopened: <count> (or "skipped")
```
```

**Step 4: Update Important Notes section**

Replace the Important Notes section with:

```markdown
## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).

Additional conventions for this skill:
- **Explicit confirmation is mandatory** for Phase 3. Never auto-proceed. Always use AskUserQuestion.
- **Sub-issues first, then parent.** This prevents the parent from being in a misleading state if something fails mid-way.
- **Project is required** for this skill. If no project config is available during setup, tell the user: "mass-update-issues requires a configured project board. Run setup first." and stop.
- **Do not fail on missing date fields.** If `clear-date` or `set-date` fails for an issue, log a warning and continue with the next issue.
```

**Step 5: Commit**

```bash
git add plugins/github-project-tools/skills/mass-update-issues/SKILL.md
git commit -m "feat(github-project-tools): rewrite mass-update skill to not require open state"
```

---

### Task 5: Verify shared prompts are unchanged

**Step 1: Verify no shared prompt changes are needed**

Check that the shared prompts (`preflight.md`, `conventions.md`, `setup.md`, `parse-issue-arg.md`) in the mass-update-issues skill directory are identical to their copies in other skills:

Run:
```bash
cd plugins/github-project-tools
diff skills/mass-update-issues/prompts/preflight.md skills/add-issue/prompts/preflight.md
diff skills/mass-update-issues/prompts/conventions.md skills/add-issue/prompts/conventions.md
diff skills/mass-update-issues/prompts/setup.md skills/add-issue/prompts/setup.md
diff skills/mass-update-issues/prompts/parse-issue-arg.md skills/start-implementing-issue/prompts/parse-issue-arg.md
```

Expected: No differences (empty output for all diffs).

No commit needed — this is a verification step only.

---

### Task 6: Run full CI checks

**Step 1: Run all checks**

Run:
```bash
cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright
```

Expected: All pass.

**Step 2: Run shellcheck**

Run:
```bash
shellcheck plugins/github-project-tools/scripts/github-project-tools.sh
```

Expected: No issues (the shell wrapper just delegates to Python, no changes needed).

No commit needed — this is a verification step only.
