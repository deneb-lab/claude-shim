# Mass-Update Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `mass-update` skill to the `github-project-tools` plugin that updates an issue and all its sub-issues' statuses, dates, and close state on the GitHub project board.

**Architecture:** Three new CLI subcommands (`list-sub-issues`, `list-status-options`, `set-status-by-option-id`) added to the existing Python CLI, plus a new skill definition (SKILL.md + shared prompt copies). The skill orchestrates user confirmation for status, dates, and close operations before executing updates on sub-issues first, then parent.

**Tech Stack:** Python (pydantic, subprocess), GitHub GraphQL API via `gh`, Claude Code skill YAML frontmatter + markdown.

---

### Task 1: Add `list-sub-issues` CLI subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add to `test_cli.py`:

```python
class TestListSubIssues:
    def test_returns_sub_issues(self, capsys: pytest.CaptureFixture[str]) -> None:
        sub_issues_json = json.dumps([
            {"id": "I_sub1", "number": 10, "title": "Sub 1", "state": "OPEN"},
            {"id": "I_sub2", "number": 11, "title": "Sub 2", "state": "CLOSED"},
        ])
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=sub_issues_json + "\n", stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "list-sub-issues", "I_parent"])
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2
        assert out[0]["id"] == "I_sub1"
        assert out[1]["state"] == "CLOSED"

    def test_returns_empty_array_when_no_sub_issues(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "list-sub-issues", "I_parent"])
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert out == []

    def test_uses_correct_jq_filter(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["--repo", "owner/repo", "list-sub-issues", "I_parent"])
        call_args = mock_run.call_args[0][0]
        assert "--jq" in call_args
        jq_idx = call_args.index("--jq")
        jq_filter = call_args[jq_idx + 1]
        assert "subIssues" in jq_filter
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestListSubIssues -v`
Expected: FAIL — `list-sub-issues` is unknown subcommand

**Step 3: Write minimal implementation**

Add to `cli.py` in the repo-only subcommands section (after `cmd_count_open_sub_issues`):

```python
def cmd_list_sub_issues(node_id: str) -> int:
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              subIssues(first: 50) {
                nodes { id number title state }
              }
            }
          }
        }""",
        {"id": node_id},
        jq_filter="[.data.node.subIssues.nodes[] | {id, number, title, state}]",
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

Add `"list-sub-issues"` to the `repo_only_cmds` set and the dispatch block:

```python
if subcmd == "list-sub-issues":
    return cmd_list_sub_issues(sub_args[0])
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestListSubIssues -v`
Expected: PASS (3 tests)

**Step 5: Run full test suite + linting**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 6: Commit**

```
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add list-sub-issues CLI subcommand"
```

---

### Task 2: Add `list-status-options` CLI subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add to `test_cli.py`:

```python
class TestListStatusOptions:
    def test_returns_status_options(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        options_json = json.dumps([
            {"id": "OPT_1", "name": "Todo"},
            {"id": "OPT_2", "name": "In Progress"},
            {"id": "OPT_3", "name": "Done"},
            {"id": "OPT_4", "name": "Blocked"},
        ])
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=options_json + "\n", stderr=""
            )
            exit_code = main(["list-status-options"], cwd=tmp_path)
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 4
        assert out[3]["name"] == "Blocked"

    def test_queries_status_field_id_from_config(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["list-status-options"], cwd=tmp_path)
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        # Should use the status field ID from config
        assert "PVTF_status" in call_str

    def test_missing_config_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="1"):
            main(["list-status-options"], cwd=tmp_path)
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestListStatusOptions -v`
Expected: FAIL — unknown subcommand

**Step 3: Write minimal implementation**

Add to `cli.py` in the config-driven section (after `cmd_set_date`):

```python
def cmd_list_status_options(config: GitHubProjectToolsConfig) -> int:
    field_id = config.fields.status.id
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on ProjectV2SingleSelectField {
              options { id name }
            }
          }
        }""",
        {"id": field_id},
        jq_filter="[.data.node.options[] | {id, name}]",
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

Add `"list-status-options"` to the `config_cmds` set and add dispatch:

```python
if subcmd == "list-status-options":
    return cmd_list_status_options(config)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestListStatusOptions -v`
Expected: PASS (3 tests)

**Step 5: Run full test suite + linting**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 6: Commit**

```
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add list-status-options CLI subcommand"
```

---

### Task 3: Add `set-status-by-option-id` CLI subcommand

**Files:**
- Modify: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- Test: `plugins/github-project-tools/hook/tests/test_cli.py`

**Step 1: Write the failing tests**

Add to `test_cli.py`:

```python
class TestSetStatusByOptionId:
    def test_sets_status_with_raw_option_id(self, tmp_path: Path) -> None:
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
                [
                    "--repo", "owner/repo",
                    "set-status-by-option-id", "PVTI_item", "OPT_custom",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        # Verify the raw option ID was used in the GraphQL call
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "OPT_custom" in call_str

    def test_uses_status_field_id_from_config(self, tmp_path: Path) -> None:
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
                [
                    "--repo", "owner/repo",
                    "set-status-by-option-id", "PVTI_item", "OPT_1",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTF_status" in call_str
```

**Step 2: Run tests to verify they fail**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetStatusByOptionId -v`
Expected: FAIL — unknown subcommand

**Step 3: Write minimal implementation**

Add to `cli.py` in the config-driven section (after `cmd_list_status_options`):

```python
def cmd_set_status_by_option_id(
    config: GitHubProjectToolsConfig,
    item_id: str,
    option_id: str,
) -> int:
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

Add `"set-status-by-option-id"` to the `config_cmds` set and add dispatch:

```python
if subcmd == "set-status-by-option-id":
    return cmd_set_status_by_option_id(config, sub_args[0], sub_args[1])
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/github-project-tools/hook && uv run pytest tests/test_cli.py::TestSetStatusByOptionId -v`
Expected: PASS (2 tests)

**Step 5: Run full test suite + linting**

Run: `cd plugins/github-project-tools/hook && uv run pytest -v && uv run ruff check && uv run ruff format --check && uv run pyright`
Expected: All pass

**Step 6: Commit**

```
git add plugins/github-project-tools/hook/src/github_project_tools/cli.py plugins/github-project-tools/hook/tests/test_cli.py
git commit -m "feat(github-project-tools): add set-status-by-option-id CLI subcommand"
```

---

### Task 4: Create skill directory and copy shared prompts

**Files:**
- Create: `plugins/github-project-tools/skills/mass-update/prompts/preflight.md` (copy from `start-implementation`)
- Create: `plugins/github-project-tools/skills/mass-update/prompts/conventions.md` (copy from `start-implementation`)
- Create: `plugins/github-project-tools/skills/mass-update/prompts/setup.md` (copy from `start-implementation`)
- Create: `plugins/github-project-tools/skills/mass-update/prompts/parse-issue-arg.md` (copy from `start-implementation`)

**Step 1: Copy prompt files**

```bash
mkdir -p plugins/github-project-tools/skills/mass-update/prompts
cp plugins/github-project-tools/skills/start-implementation/prompts/preflight.md plugins/github-project-tools/skills/mass-update/prompts/
cp plugins/github-project-tools/skills/start-implementation/prompts/conventions.md plugins/github-project-tools/skills/mass-update/prompts/
cp plugins/github-project-tools/skills/start-implementation/prompts/setup.md plugins/github-project-tools/skills/mass-update/prompts/
cp plugins/github-project-tools/skills/start-implementation/prompts/parse-issue-arg.md plugins/github-project-tools/skills/mass-update/prompts/
```

**Step 2: Verify copies are identical**

```bash
diff plugins/github-project-tools/skills/start-implementation/prompts/preflight.md plugins/github-project-tools/skills/mass-update/prompts/preflight.md
diff plugins/github-project-tools/skills/start-implementation/prompts/conventions.md plugins/github-project-tools/skills/mass-update/prompts/conventions.md
diff plugins/github-project-tools/skills/start-implementation/prompts/setup.md plugins/github-project-tools/skills/mass-update/prompts/setup.md
diff plugins/github-project-tools/skills/start-implementation/prompts/parse-issue-arg.md plugins/github-project-tools/skills/mass-update/prompts/parse-issue-arg.md
```

Expected: No diff output (identical files)

**Step 3: Commit**

```
git add plugins/github-project-tools/skills/mass-update/prompts/
git commit -m "feat(github-project-tools): copy shared prompts for mass-update skill"
```

---

### Task 5: Write the SKILL.md

**Files:**
- Create: `plugins/github-project-tools/skills/mass-update/SKILL.md`

**Step 1: Write the skill definition**

Create `plugins/github-project-tools/skills/mass-update/SKILL.md` with this content:

````markdown
---
name: mass-update
description: Update an issue and all its sub-issues - sets status, dates, and close state on the project board
allowed-tools: Bash(*/github-project-tools/scripts/github-project-tools.sh preflight), Bash(*/github-project-tools/scripts/github-project-tools.sh read-config), Bash(*/github-project-tools/scripts/github-project-tools.sh repo-detect), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-view-full *), Bash(*/github-project-tools/scripts/github-project-tools.sh list-sub-issues *), Bash(*/github-project-tools/scripts/github-project-tools.sh list-status-options *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-project-item *), Bash(*/github-project-tools/scripts/github-project-tools.sh add-to-project *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status-by-option-id *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-status *), Bash(*/github-project-tools/scripts/github-project-tools.sh set-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-close *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *), Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *)
---

# GitHub Projects — Mass Update

Update an issue and all its sub-issues on the project board: set status, dates, and optionally close them.

## Phase 0: Preflight

Follow the steps in [prompts/preflight.md](prompts/preflight.md).

All CLI commands below use `<cli>` to mean the invocation pattern established during preflight.

## Phase 1: Setup

Follow the steps in [prompts/setup.md](prompts/setup.md).

## Phase 2: Fetch Issue & Sub-issues

1. Follow the steps in [prompts/parse-issue-arg.md](prompts/parse-issue-arg.md).

   **Important:** The user may also provide a logical state hint after the issue number/URL (e.g., `73 todo` or `https://...issues/73 done`). Extract and save this as `STATE_HINT` if present. Valid hints are: `todo`, `in-progress`, `done`. Anything else is not a hint — ignore it.

2. Fetch the issue details:
   ```bash
   <cli> issue-view-full <number>
   ```
   Save the JSON output. Extract the issue `id` as `NODE_ID`, `title`, `body`, and `state`.

3. Verify the issue is open. If `state` is not `OPEN`, tell the user the issue is closed and stop.

4. Fetch sub-issues:
   ```bash
   <cli> list-sub-issues "$NODE_ID"
   ```
   Save the JSON array as `SUB_ISSUES`. Each element has `id`, `number`, `title`, `state`.

5. Display to the user:
   ```
   Issue #<number>: <title>
   Found <count> sub-issues:
   - #<sub_number>: <sub_title> (<sub_state>)
   - ...
   ```

   If there are no sub-issues, tell the user and continue (the skill can still update the parent issue alone).

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

7. Confirm the final choice: "Will set status to `<name>` (option ID: `<OPTION_ID>`) on #<number> and <count> sub-issues. Proceed?"
   - **Wait for explicit confirmation before continuing.**

## Phase 4: Determine Date Handling

**User confirmation is MANDATORY. NEVER skip the prompt.**

This phase only applies when `LOGICAL_STATE` is `"todo"` or `"done"`. If `LOGICAL_STATE` is `"in-progress"` or null, **skip this phase entirely** but **tell the user** you're skipping it: "Skipping date handling (not applicable for `<status>` status)."

1. Determine which date field applies:
   - `"todo"` → start date (`START_FIELD`)
   - `"done"` → end date (`END_FIELD`)

2. **Prompt the user using AskUserQuestion:**
   - For "todo": "Set **start date** (today) on which issues?"
   - For "done": "Set **end date** (today) on which issues?"

   Options:
   a. Set date on parent issue only
   b. Set date on parent and sub-issues (Recommended)
   c. Set date on sub-issues only
   d. Do not set dates

3. Save the user's choice as `DATE_SCOPE` (one of: `parent-only`, `parent-and-subs`, `subs-only`, `none`).

4. **Important rule:** When executing date updates in Phase 6, **never overwrite an existing date**. Check each issue's current date before setting. If a date is already set, skip that issue silently.

## Phase 5: Determine Close Handling

**User confirmation is MANDATORY. NEVER skip the prompt.**

This phase only applies when `LOGICAL_STATE` is `"done"`. If `LOGICAL_STATE` is not `"done"`, **skip this phase entirely** but **tell the user** you're skipping it: "Skipping close handling (not applicable for `<status>` status)."

1. **Prompt the user using AskUserQuestion:**
   "Close #<number> and all its sub-issues?"

   Options:
   a. Yes, close all
   b. No, only update status and dates

2. Save the user's choice as `CLOSE_ISSUES` (boolean).

## Phase 6: Execute Updates

**Order: sub-issues first, then parent.**

For each issue in the update list (all sub-issues, then the parent issue):

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

3. **Set date** (if `DATE_SCOPE` applies to this issue):
   - Determine if this issue is in scope based on `DATE_SCOPE`:
     - `parent-only`: only the parent issue
     - `parent-and-subs`: all issues
     - `subs-only`: only sub-issues
     - `none`: skip all
   - If in scope, check current date:
     ```bash
     <cli> get-start-date "$ISSUE_NODE_ID"
     ```
     Extract the date. If it is `null` (no date set), set it:
     ```bash
     <cli> set-date "$ISSUE_ITEM_ID" "$DATE_FIELD_ID"
     ```
     If a date is already set, skip silently.

     Note: `get-start-date` checks the start date field. For end dates, there is no `get-end-date` subcommand. For end dates, use the same `get-start-date` logic but note it only checks start dates. Since `set-date` accepts any field ID, pass `END_FIELD` for done states. To check existing end dates, query the project item's field values — but since there's no dedicated subcommand, **always set end dates** (the GraphQL mutation is idempotent — setting the same date again is harmless).

4. **Close issue** (if `CLOSE_ISSUES` is true):
   ```bash
   <cli> issue-close <issue_number>
   ```

5. **Report progress** after each issue:
   ```
   Updated #<number> (<title>): status → <status_name>
   ```

After all updates complete, display a summary:
```
Mass update complete:
- Status: <status_name>
- Issues updated: <count>
- Dates set: <count> (or "skipped")
- Issues closed: <count> (or "skipped")
```

## Important Notes

Follow the conventions in [prompts/conventions.md](prompts/conventions.md).

Additional conventions for this skill:
- **Explicit confirmation is mandatory** for Phases 3, 4, and 5. Never auto-proceed. Always use AskUserQuestion.
- **Sub-issues first, then parent.** This prevents the parent from being in a misleading state if something fails mid-way.
- **Never overwrite existing dates.** Check before setting.
- **Project is required** for this skill. If no project config is available during setup, tell the user: "mass-update requires a configured project board. Run setup first." and stop.
````

**Step 2: Review the skill file**

Read the file back and verify:
- Frontmatter has correct `name`, `description`, and `allowed-tools`
- All phases reference correct subcommands
- All prompts are linked correctly

**Step 3: Commit**

```
git add plugins/github-project-tools/skills/mass-update/SKILL.md
git commit -m "feat(github-project-tools): add mass-update skill definition"
```

---

### Task 6: Update shared prompt references and CLAUDE.md

**Files:**
- Modify: `plugins/github-project-tools/CLAUDE.md`

**Step 1: Read current CLAUDE.md**

Read: `plugins/github-project-tools/CLAUDE.md`

**Step 2: Update shared prompt documentation**

Update the CLAUDE.md to mention that `mass-update` now also shares `preflight.md`, `conventions.md`, `setup.md`, and `parse-issue-arg.md`. Specifically update:
- The skill count (from "Four skills" to "Five skills")
- Add `mass-update` to the list of skills
- Update shared prompt documentation to include `mass-update` as sharing all four prompt files

**Step 3: Commit**

```
git add plugins/github-project-tools/CLAUDE.md
git commit -m "docs(github-project-tools): add mass-update to shared prompt docs"
```

---

### Task 7: Version bump and marketplace update

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current versions**

Read both files. Current version is `2.9.1`.

**Step 2: Bump to `2.10.0`** (minor bump — new feature)

In `plugins/github-project-tools/.claude-plugin/plugin.json`, change `"version": "2.9.1"` to `"version": "2.10.0"`.

In `.claude-plugin/marketplace.json`:
- Change the github-project-tools entry `"version": "2.9.1"` to `"version": "2.10.0"`
- Bump `metadata.version` from `"1.0.13"` to `"1.0.14"`

**Step 3: Run JSON validation**

```bash
jq . plugins/github-project-tools/.claude-plugin/plugin.json
jq . .claude-plugin/marketplace.json
```

Expected: Valid JSON output, no errors

**Step 4: Commit**

```
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v2.10.0: add mass-update skill"
```

---

### Task 8: Final verification

**Step 1: Run full test suite**

```bash
cd plugins/github-project-tools/hook && uv run pytest -v
```

Expected: All tests pass (existing + 8 new tests from Tasks 1-3)

**Step 2: Run all linters**

```bash
cd plugins/github-project-tools/hook && uv run ruff check && uv run ruff format --check && uv run pyright
```

Expected: Clean

**Step 3: Verify shared prompt sync**

```bash
for f in preflight.md conventions.md setup.md parse-issue-arg.md; do
  echo "=== $f ==="
  diff plugins/github-project-tools/skills/start-implementation/prompts/$f plugins/github-project-tools/skills/mass-update/prompts/$f
done
```

Expected: No diff output

**Step 4: Verify all new files exist**

```bash
ls -la plugins/github-project-tools/skills/mass-update/SKILL.md
ls -la plugins/github-project-tools/skills/mass-update/prompts/
```

Expected: SKILL.md and 4 prompt files present

**Step 5: Verify JSON files**

```bash
jq . plugins/github-project-tools/.claude-plugin/plugin.json
jq . .claude-plugin/marketplace.json
```

Expected: Valid JSON, versions match (2.10.0 in both)
