The script auto-detects the current repository from the git remote. When `REPO_OVERRIDE` is set (see issue-fetching phase), pass `--repo $REPO_OVERRIDE` before the subcommand in every script invocation to override auto-detection.

1. Get project fields (date field IDs):
   ```bash
   <resolved-path> get-project-fields
   ```
   This returns JSON with `start` and `end` field IDs. Save these as `START_FIELD` and `END_FIELD`.

   If this command fails because no project is found, note that **no project is available**. Skip all project operations (get-project-item, add-to-project, set-date, set-status) in later phases. Continue with issue-only operations.

2. The `set-status` subcommand accepts the literal arguments `todo`, `in-progress`, and `done` directly — no manual mapping of project-specific status names is needed.
