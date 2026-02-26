1. Find the bundled setup script. Use Glob to locate it:
   ```
   ~/.claude/plugins/**/quality-check-hook/scripts/setup-quality-check-hook.sh
   ```
2. Store the resolved absolute path — use it as the literal first token in every Bash command for the rest of this skill.
   For example, if the script is at `/home/user/.claude/plugins/cache/claude-shim-marketplace/quality-check-hook/1.0.1/scripts/setup-quality-check-hook.sh`, then all commands should start with that full path.
3. Run the uv check:
   ```bash
   <resolved-path> check-uv
   ```
4. If the command fails, stop and tell the user:

   > The quality-check-hook plugin requires uv to run. Install it with:
   > `curl -LsSf https://astral.sh/uv/install.sh | sh`
   > See https://docs.astral.sh/uv/getting-started/installation/ for other methods.

   Do not proceed until `uv` is available.
