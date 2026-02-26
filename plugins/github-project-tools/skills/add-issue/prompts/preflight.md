1. Find the bundled script. Use Glob to locate it:
   ```
   ~/.claude/plugins/**/github-project-tools/scripts/github-projects.sh
   ```
2. Store the resolved absolute path — use it as the literal first token in every Bash command for the rest of this skill.
   For example, if the script is at `/home/user/.claude/plugins/cache/claude-shim-marketplace/github-project-tools/1.0.0/scripts/github-projects.sh`, then run commands like `<resolved-path> preflight`.
3. Run preflight checks:
   ```bash
   <resolved-path> preflight
   ```
4. If preflight fails, stop and show the error message to the user. Do not proceed.
