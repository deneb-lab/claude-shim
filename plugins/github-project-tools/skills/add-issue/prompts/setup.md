The CLI auto-detects the current repository from the git remote. When `REPO_OVERRIDE` is set (see issue-fetching phase), pass `--repo $REPO_OVERRIDE` before the subcommand in every CLI invocation to override auto-detection.

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
