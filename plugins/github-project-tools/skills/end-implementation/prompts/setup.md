The CLI auto-detects the current repository from the git remote. When `REPO_OVERRIDE` is set, pass `--repo $REPO_OVERRIDE` before the subcommand in every CLI invocation to override auto-detection.

1. Read the project config:
   ```bash
   <cli> read-config
   ```

   - **If the command succeeds** (exit code 0), it outputs JSON. Extract and save:
     - `START_FIELD` from `.fields.start-date`
     - `END_FIELD` from `.fields.end-date`
     - The `set-status` subcommand accepts `todo`, `in-progress`, and `done` directly — no manual mapping needed.
     - Note that **a project is available** — proceed with project operations in later phases.

   - **If the command fails** (exit code 1), no config is available. Tell the user:
     "No github-project-tools configuration found. Running setup."
     Then invoke the `github-project-tools:setup-github-project-tools` skill via the Skill tool.
     After setup completes, re-run `<cli> read-config` and extract the values above.

2. Check the `repo` field in the config output:

   - **If `repo` is present** (not null): Use it as `REPO_OVERRIDE` for all subsequent CLI commands. Pass `--repo $REPO_OVERRIDE` before the subcommand in every invocation.

   - **If `repo` is null or missing:**
     1. Detect the current repository:
        ```bash
        <cli> repo-detect
        ```
     2. Use AskUserQuestion to ask: "No repository configured in `.claude-shim.json`. Detected: `<detected-repo>`. Use this repository for issue operations?"
        - **Yes, use this repository** — save as `REPO_OVERRIDE`.
        - **No, let me specify** — ask the user for the correct `owner/repo` value. Save as `REPO_OVERRIDE`.
     3. Read `.claude-shim.json`, add the `repo` field to the `github-project-tools` key with the confirmed value, preserve all other keys, and write back using the Write tool.
     4. Use AskUserQuestion to ask: "Updated `.claude-shim.json` with repo. Commit the change?"
        - If yes: commit the file.
        - If no: leave uncommitted.
     5. Use the confirmed repo as `REPO_OVERRIDE` going forward.

   **Never continue to the next phase without `REPO_OVERRIDE` set.**
