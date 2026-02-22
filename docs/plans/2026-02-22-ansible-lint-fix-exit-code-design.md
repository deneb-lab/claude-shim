# Design: ansible-lint --fix non-zero exit code handling

**Issue:** [#11](https://github.com/elahti/claude-shim/issues/11)
**Date:** 2026-02-22

## Problem

`ansible-lint --fix` exits with a non-zero exit code even when it successfully auto-fixes issues. The quality-check-hook runner stops on the first non-zero exit code, so the subsequent validation-only `ansible-lint` pass never runs.

## Solution

Special-case `ansible-lint --fix` in `runner.py`. When a command starts with `ansible-lint --fix` and returns non-zero, silently continue to the next command instead of returning failure.

No config schema changes. No new config options. The subsequent `ansible-lint` (validation-only) command remains the pass/fail gate.

## Changes

- **`runner.py`**: In `run_commands()`, add a check in the `if result.returncode != 0:` block. If the command starts with `"ansible-lint --fix"`, continue the loop instead of returning failure.
- **`test_runner.py`**: Add test case for ansible-lint --fix non-zero exit continuing execution.
