1. Find the bundled CLI wrapper. Use Glob to locate it:
   ```
   ~/.claude/plugins/**/github-project-tools/scripts/github-project-tools.sh
   ```
   Store the matched path as `CLI_PATH`. For example, if the match is `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/2.1.0/scripts/github-project-tools.sh`, then `CLI_PATH` is that full path.

2. All commands for the rest of this skill use this invocation pattern:
   ```bash
   <CLI_PATH> <subcommand> [args...]
   ```
   Referred to as `<cli> <subcommand>` in the rest of this document.

3. Run preflight checks:
   ```bash
   <cli> preflight
   ```
4. If preflight fails, stop and show the error message to the user. Do not proceed.
