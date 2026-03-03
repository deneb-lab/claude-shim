# End-Implementation Skill Improvements — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bring the `end-implementation` skill in line with the expected workflow from issue #76 — add start date checks, assignment checks, always-available closing comments with git log, and parent assignment checks.

**Architecture:** Skill-first approach. Update the SKILL.md with all new workflow steps, add two new CLI subcommands (`issue-get-assignees`, `get-status-change-date`), remove two unused ones (`issue-edit`, `table-set-status`), and update allowed-tools.

**Tech Stack:** Python CLI (pydantic, pytest, pyright, ruff), Markdown skills, GitHub GraphQL + REST APIs via `gh` CLI.

**Key paths:**
- CLI source: `plugins/github-project-tools/hook/src/github_project_tools/cli.py`
- CLI tests: `plugins/github-project-tools/hook/tests/test_cli.py`
- Skill: `plugins/github-project-tools/skills/end-implementation/SKILL.md`
- All paths below are relative to `plugins/github-project-tools/` in the repo root at `/home/esko/.claude/plugins/marketplaces/claude-shim-marketplace/`

---

### Task 1: Remove `issue-edit` CLI subcommand

**Files:**
- Modify: `hook/src/github_project_tools/cli.py` (remove `cmd_issue_edit` function ~lines 266-282, remove from `issue_cmds` set ~line 604, remove dispatch ~lines 618-619)
- Modify: `hook/tests/test_cli.py` (remove `TestIssueEdit` class ~lines 216-245)

**Step 1: Delete the `cmd_issue_edit` function**

Remove the entire `cmd_issue_edit` function from `cli.py`.

**Step 2: Remove from dispatch**

In `main()`, remove `"issue-edit"` from the `issue_cmds` set and remove the `if subcmd == "issue-edit"` dispatch block.

**Step 3: Delete tests**

Remove the `TestIssueEdit` class from `test_cli.py`.

**Step 4: Run tests**

Run: `cd hook && uv run pytest tests/ -v`
Expected: All tests pass. No tests reference `issue-edit`.

**Step 5: Run linting and type checks**

Run: `cd hook && uv run ruff check src/ tests/ && uv run pyright`
Expected: Clean.

**Step 6: Commit**

```bash
git add -A plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): remove unused issue-edit subcommand"
```

---

### Task 2: Remove `table-set-status` CLI subcommand

**Files:**
- Modify: `hook/src/github_project_tools/cli.py` (remove `cmd_table_set_status` function ~lines 516-557, remove from `repo_only_cmds` set ~line 654, remove dispatch ~lines 665-668)
- Modify: `hook/tests/test_cli.py` (remove `TestTableSetStatus` class ~lines 691-762)

**Step 1: Delete the `cmd_table_set_status` function**

Remove the entire `cmd_table_set_status` function from `cli.py`. Also check if the `re` import is still needed after removal — if nothing else uses `re`, remove the import too.

**Step 2: Remove from dispatch**

In `main()`, remove `"table-set-status"` from the `repo_only_cmds` set and remove the `if subcmd == "table-set-status"` dispatch block.

**Step 3: Delete tests**

Remove the `TestTableSetStatus` class from `test_cli.py`.

**Step 4: Run tests**

Run: `cd hook && uv run pytest tests/ -v`
Expected: All tests pass.

**Step 5: Run linting and type checks**

Run: `cd hook && uv run ruff check src/ tests/ && uv run pyright`
Expected: Clean.

**Step 6: Commit**

```bash
git add -A plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): remove unused table-set-status subcommand"
```

---

### Task 3: Add `issue-get-assignees` CLI subcommand

**Files:**
- Modify: `hook/src/github_project_tools/cli.py`
- Modify: `hook/tests/test_cli.py`

**Step 1: Write the failing test**

Add a `TestIssueGetAssignees` class to `test_cli.py`:

```python
class TestIssueGetAssignees:
    def test_returns_assignee_logins(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='["elahti","other-user"]\n',
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "issue-get-assignees", "42"]
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "elahti" in out
        assert "other-user" in out
        call_args = mock_run.call_args[0][0]
        assert "issue" in call_args
        assert "view" in call_args
        assert "42" in call_args
        assert "assignees" in call_args

    def test_returns_empty_array_when_unassigned(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="[]\n",
                stderr="",
            )
            exit_code = main(
                ["--repo", "owner/repo", "issue-get-assignees", "42"]
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "[]" in out
```

**Step 2: Run test to verify it fails**

Run: `cd hook && uv run pytest tests/test_cli.py::TestIssueGetAssignees -v`
Expected: FAIL — `Unknown subcommand: issue-get-assignees`

**Step 3: Write the implementation**

Add to `cli.py`:

```python
def cmd_issue_get_assignees(repo: str, number: str) -> int:
    result = run_gh(
        [
            "issue",
            "view",
            number,
            "--repo",
            repo,
            "--json",
            "assignees",
            "--jq",
            "[.assignees[].login]",
        ]
    )
    if result.stdout:
        print(result.stdout, end="")
    return 0
```

Register in `main()`:
- Add `"issue-get-assignees"` to the `issue_cmds` set
- Add dispatch: `if subcmd == "issue-get-assignees": return cmd_issue_get_assignees(resolved_repo, sub_args[0])`

**Step 4: Run tests**

Run: `cd hook && uv run pytest tests/test_cli.py::TestIssueGetAssignees -v`
Expected: PASS

**Step 5: Run full test suite + linting**

Run: `cd hook && uv run pytest tests/ -v && uv run ruff check src/ tests/ && uv run pyright`
Expected: All clean.

**Step 6: Commit**

```bash
git add -A plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): add issue-get-assignees subcommand"
```

---

### Task 4: Add `get-status-change-date` CLI subcommand

**Files:**
- Modify: `hook/src/github_project_tools/cli.py`
- Modify: `hook/tests/test_cli.py`

**Context:** This subcommand returns the date when the issue was added to the project board (as a proxy for when it was set to "In Progress"). Uses the `AddedToProjectV2Event` timeline event via GraphQL. Returns the date string (YYYY-MM-DD) or `null`.

**Step 1: Write the failing test**

Add a `TestGetStatusChangeDate` class to `test_cli.py`:

```python
class TestGetStatusChangeDate:
    def test_returns_date_from_timeline(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                # get_project_id call
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                # GraphQL timeline query
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="2024-02-20\n",
                    stderr="",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-status-change-date", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out.strip()
        assert out == "2024-02-20"

    def test_returns_null_when_no_events(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                # get_project_id call
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                # GraphQL timeline query — no matching events
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="",
                    stderr="",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-status-change-date", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out.strip()
        assert out == "null"
```

**Step 2: Run test to verify it fails**

Run: `cd hook && uv run pytest tests/test_cli.py::TestGetStatusChangeDate -v`
Expected: FAIL

**Step 3: Write the implementation**

Add to `cli.py`:

```python
def cmd_get_status_change_date(
    config: GitHubProjectToolsConfig, node_id: str
) -> int:
    """Get date when issue was added to project (proxy for 'in progress' date)."""
    project_id = get_project_id(config)
    result = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              timelineItems(first: 100, itemTypes: [ADDED_TO_PROJECT_V2_EVENT]) {
                nodes {
                  ... on AddedToProjectV2Event {
                    createdAt
                    project { id }
                  }
                }
              }
            }
          }
        }""",
        {"id": node_id},
        jq_filter=(
            "[.data.node.timelineItems.nodes[]"
            f' | select(.project.id == "{project_id}")'
            " | .createdAt[:10]] | last"
        ),
    )
    out = result.stdout.strip() if result.stdout else ""
    if out and out != "null":
        print(out)
    else:
        print("null")
    return 0
```

Register in `main()`:
- Add `"get-status-change-date"` to the `config_cmds` set
- Add dispatch: `if subcmd == "get-status-change-date": return cmd_get_status_change_date(config, sub_args[0])`

**Step 4: Run tests**

Run: `cd hook && uv run pytest tests/test_cli.py::TestGetStatusChangeDate -v`
Expected: PASS

**Step 5: Verify against live API**

Run the subcommand against a real issue that's on the project board to confirm the GraphQL query works:

```bash
<cli> --repo elahti/deneb-marketplace get-status-change-date "I_kwDORWuxZ87vS0AH"
```

If the `AddedToProjectV2Event` timeline event type is not supported, adjust the GraphQL query. The fallback is to return `null` (the skill will suggest today's date instead).

**Step 6: Run full suite + linting**

Run: `cd hook && uv run pytest tests/ -v && uv run ruff check src/ tests/ && uv run pyright`
Expected: All clean.

**Step 7: Commit**

```bash
git add -A plugins/github-project-tools/hook/
git commit -m "feat(github-project-tools): add get-status-change-date subcommand"
```

---

### Task 5: Update SKILL.md — Add Phase 2.3 (pre-close checks)

**Files:**
- Modify: `skills/end-implementation/SKILL.md`

**Step 1: Update handoff skip target**

Change Phase 1 text from "skip to Phase 2.5" to "skip to Phase 2.3" (both the Phase 1 and Phase 2 skip instructions).

**Step 2: Add Phase 2.3 section**

Insert after Phase 2 and before Phase 2.5:

```markdown
## Phase 2.3: Pre-Close Checks

These checks ensure the issue is in a clean state before closing.

1. **If a project is available**, check if the issue has a start date:
   ```bash
   <cli> get-start-date "$NODE_ID"
   ```
   - If the output is **non-empty** and the `.date` field is **not `null`**: start date is already set. Skip to step 2.
   - If the output is **empty** or `.date` is `null`: no start date. Try to auto-detect one:
     ```bash
     <cli> get-status-change-date "$NODE_ID"
     ```
     - If the output is a date (not `null`): suggest that date.
     - If the output is `null`: suggest today's date.
     - **Ask the user:** "Issue has no start date. Set to <suggested date>?"
     - If confirmed:
       - Get the ITEM_ID if not already known:
         ```bash
         <cli> get-project-item "$NODE_ID"
         ```
       - Set the start date:
         ```bash
         <cli> set-date "$ITEM_ID" "$START_FIELD" <date>
         ```

2. Check if the current user is assigned to the issue:
   ```bash
   <cli> issue-get-assignees <number>
   ```
   Check if the current user's login is in the returned JSON array. To determine the current user, the login used during `gh auth status` is available — or simply check if the array is non-empty (if no one is assigned, offer to assign).
   - If the user is **not** in the assignees list: **Ask the user:** "Assign yourself to #<number>?"
   - If confirmed:
     ```bash
     <cli> issue-assign <number>
     ```
```

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): add pre-close checks phase to end-implementation"
```

---

### Task 6: Update SKILL.md — Revise Phase 2.5 (closing comment)

**Files:**
- Modify: `skills/end-implementation/SKILL.md`

**Step 1: Replace Phase 2.5**

Replace the entire Phase 2.5 section with:

```markdown
## Phase 2.5: Closing Comment

Generate an optional closing comment summarizing what was implemented. This provides context for future sessions reviewing this issue.

1. **Determine available context:**

   - **Check git state:** Run `git rev-parse --abbrev-ref HEAD` to get the current branch. If the branch is not `main` (or the default branch), there may be relevant commits.
   - **If on a non-main branch:** Run `git log main..HEAD --oneline` to get the commit list. Cross-check these commits against the issue title and body to determine relevance. If unsure whether the commits relate to this issue, ask the user.
   - **Conversation context:** If this is a handoff from `start-implementation` (implementation work was done in this session), also use the conversation context — what was discussed, built, and changed.

2. **Generate a summary** using the available context (conversation + git log):

   ```markdown
   ## Implementation Summary

   - <what was done, 3-7 bullets>
   ```

   Each bullet should describe a concrete change. Focus on what changed, not why.

   - If there is **no usable context** (on main branch, no relevant commits, no conversation context): skip the auto-generated summary and go directly to step 3.

3. **Present to the user:**
   - If a summary was generated: "Here's the closing comment that will be posted:" followed by the summary. Ask: **"Post this as a closing comment? (You can also edit it, write your own, or skip.)"**
   - If no summary was generated: **"Would you like to add a closing comment before closing the issue? (You can write one or skip.)"**
   - **If approved (or user provides custom text):** Save as `SUMMARY` for use in Phase 3.
   - **If skipped:** Set `SUMMARY` to empty. The issue will be closed without a comment.
```

**Step 2: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): revise closing comment to work in both modes"
```

---

### Task 7: Update SKILL.md — Add parent assignment check + update allowed-tools

**Files:**
- Modify: `skills/end-implementation/SKILL.md`

**Step 1: Add parent assignment check**

In Phase 3, after the existing parent sub-issue handling (step 3), add a new step 4 before the final report step:

```markdown
4. **If a parent issue exists**, check parent assignment:
   ```bash
   <cli> issue-get-assignees <PARENT_NUMBER>
   ```
   - If the current user is **not** in the assignees list: **Ask the user:** "Assign yourself to parent #PARENT_NUMBER (PARENT_TITLE)?"
   - If confirmed:
     ```bash
     <cli> issue-assign <PARENT_NUMBER>
     ```
```

Renumber the existing final step ("Tell the user the issue is implemented and closed") to step 5.

**Step 2: Update allowed-tools in frontmatter**

Add these to the `allowed-tools` line in the YAML frontmatter:
- `Bash(*/github-project-tools/scripts/github-project-tools.sh get-start-date *)`
- `Bash(*/github-project-tools/scripts/github-project-tools.sh get-status-change-date *)`
- `Bash(*/github-project-tools/scripts/github-project-tools.sh issue-get-assignees *)`
- `Bash(*/github-project-tools/scripts/github-project-tools.sh issue-assign *)`

**Step 3: Commit**

```bash
git add plugins/github-project-tools/skills/end-implementation/SKILL.md
git commit -m "feat(github-project-tools): add parent assignment check and update allowed-tools"
```

---

### Task 8: Update shared prompts across skills

**Files:**
- Check: All copies of shared prompts across skills (preflight.md, conventions.md, setup.md, parse-issue-arg.md)

**Step 1: Verify shared prompt copies are in sync**

The CLAUDE.md states: "When editing a shared prompt, update every copy across all skills that use it." Since we're not modifying shared prompts in this work, just verify they're currently in sync:

```bash
diff plugins/github-project-tools/skills/end-implementation/prompts/preflight.md plugins/github-project-tools/skills/start-implementation/prompts/preflight.md
diff plugins/github-project-tools/skills/end-implementation/prompts/conventions.md plugins/github-project-tools/skills/start-implementation/prompts/conventions.md
diff plugins/github-project-tools/skills/end-implementation/prompts/setup.md plugins/github-project-tools/skills/start-implementation/prompts/setup.md
diff plugins/github-project-tools/skills/end-implementation/prompts/parse-issue-arg.md plugins/github-project-tools/skills/start-implementation/prompts/parse-issue-arg.md
```

Expected: No differences. If there are differences, align them.

**Step 2: No commit needed** (unless differences were found and fixed).

---

### Task 9: Version bump and release prep

**Files:**
- Modify: `plugins/github-project-tools/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json` (repo root)

**Step 1: Determine version bump**

Current version is `2.5.0`. This adds new features (CLI subcommands, skill workflow changes) and removes unused subcommands. Bump to `2.6.0` (minor version for new features).

**Step 2: Bump plugin.json**

Update `version` in `plugins/github-project-tools/.claude-plugin/plugin.json` from `2.5.0` to `2.6.0`.

**Step 3: Bump marketplace.json**

Update the matching entry in `.claude-plugin/marketplace.json` to `2.6.0`. Also bump `metadata.version` if it changed.

**Step 4: Commit**

```bash
git add plugins/github-project-tools/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release github-project-tools v2.6.0: improve end-implementation skill workflow"
```

**Step 5: Tag**

Generate release notes from commits since last tag:
```bash
git log $(git describe --tags --match 'github-project-tools/v*' --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --pretty=format:'- %s' -- plugins/github-project-tools/
```

Create annotated tag:
```bash
git tag -a github-project-tools/v2.6.0 -m "<release-notes>"
```

**Step 6: Push tag**

```bash
git push origin github-project-tools/v2.6.0
```
