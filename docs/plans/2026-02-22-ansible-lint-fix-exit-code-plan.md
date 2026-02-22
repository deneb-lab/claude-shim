# ansible-lint --fix Exit Code Handling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow `ansible-lint --fix` to exit non-zero without blocking the quality-check-hook runner.

**Architecture:** Add a special-case check in `run_commands()` that skips failure handling when the command starts with `ansible-lint --fix`. No config or schema changes.

**Tech Stack:** Python, pytest, subprocess

---

### Task 1: Add failing test for ansible-lint --fix non-zero exit

**Files:**
- Modify: `plugins/quality-check-hook/hook/tests/test_runner.py:76`

**Step 1: Write the failing test**

Add this test at the end of the `TestRunCommands` class:

```python
    def test_ansible_lint_fix_nonzero_continues_execution(self, tmp_path: Path) -> None:
        """ansible-lint --fix may exit non-zero after successful fixes; runner should continue."""
        test_file = tmp_path / "main.yml"
        test_file.write_text("content")

        with patch("quality_check_hook.runner.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="Modified 1 file.\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            result = run_commands(
                ["ansible-lint --fix", "ansible-lint"], str(test_file), cwd=str(tmp_path)
            )

        assert result.success
        assert mock_run.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/quality-check-hook/hook && uv run pytest tests/test_runner.py::TestRunCommands::test_ansible_lint_fix_nonzero_continues_execution -v`

Expected: FAIL — `assert result.success` fails because runner stops on ansible-lint --fix's non-zero exit.

---

### Task 2: Implement the fix in runner.py

**Files:**
- Modify: `plugins/quality-check-hook/hook/src/quality_check_hook/runner.py:36-41`

**Step 1: Add the special-case check**

Replace the existing `if result.returncode != 0:` block (lines 36-41) with:

```python
        if result.returncode != 0:
            if command.startswith("ansible-lint --fix"):
                continue
            output = (result.stdout + result.stderr).strip()
            return CommandResult(
                success=False,
                error_message=f"Command failed: {command}\n{output}",
            )
```

**Step 2: Run the new test to verify it passes**

Run: `cd plugins/quality-check-hook/hook && uv run pytest tests/test_runner.py::TestRunCommands::test_ansible_lint_fix_nonzero_continues_execution -v`

Expected: PASS

**Step 3: Run all tests to verify no regressions**

Run: `cd plugins/quality-check-hook/hook && uv run pytest -v`

Expected: All tests pass.

---

### Task 3: Run quality checks and commit

**Step 1: Run full quality check suite**

Run: `cd plugins/quality-check-hook/hook && uv run ruff check && uv run ruff format --check && uv run pyright`

Expected: All pass, no issues.

**Step 2: Commit**

```bash
git add plugins/quality-check-hook/hook/src/quality_check_hook/runner.py plugins/quality-check-hook/hook/tests/test_runner.py
git commit -m "fix(quality-check-hook): allow ansible-lint --fix non-zero exit code"
```
