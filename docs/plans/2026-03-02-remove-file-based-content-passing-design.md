# Design: Remove file-based content passing from github-project-tools

**Issue:** [#72](https://github.com/elahti/deneb-marketplace/issues/72) — Do not create temporary file as part of end-implementation

**Date:** 2026-03-02

## Problem

The end-implementation skill writes the implementation summary to a hardcoded path (`/tmp/issue-close-comment.md`) before closing an issue. When multiple Claude sessions close issues concurrently, they overwrite each other's temp files, causing wrong release comments on wrong issues.

## Solution

Remove all file-based content flags from the CLI and update skills to pass content inline.

## Changes

### CLI (`cli.py`)

1. **`cmd_issue_close`**: Remove `--comment-file` flag. Keep only `--comment`. Simplify the "already closed" branch to use `gh issue comment --body` inline instead of `--body-file`.

2. **`cmd_issue_create`**: Remove `--body-file` flag. Keep only `--body`.

3. **`cmd_issue_edit`**: Remove `--body-file` flag. Keep only `--body`.

### Skills

4. **`end-implementation/SKILL.md`** (lines 98-103): Replace temp file instructions with inline `--comment`:
   ```
   <cli> issue-close <number> --comment "SUMMARY text"
   ```

### Conventions

5. **`conventions.md`** (all 4 copies): Remove the `--body-file` guidance. Replace with guidance about using `--comment` or `--body` inline.

### Tests

6. **`test_cli.py`**: Remove tests for `--body-file` and `--comment-file`. Add/update tests for inline-only behavior.
