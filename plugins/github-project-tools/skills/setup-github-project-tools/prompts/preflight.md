1. Find the bundled hook project. Use Glob to locate it:
   ```
   ~/.claude/plugins/**/github-project-tools/hook/pyproject.toml
   ```
   Store the **parent directory** of the matched `pyproject.toml` as `HOOK_PATH`. For example, if the match is `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/1.1.0/hook/pyproject.toml`, then `HOOK_PATH` is `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/1.1.0/hook`.

2. All commands for the rest of this skill use this invocation pattern:
   ```bash
   uv run --project <HOOK_PATH> python -m github_project_tools <subcommand> [args...]
   ```
   Referred to as `<cli> <subcommand>` in the rest of this document.

3. Run preflight checks:
   ```bash
   <cli> preflight
   ```
4. If preflight fails, stop and show the error message to the user. Do not proceed.
