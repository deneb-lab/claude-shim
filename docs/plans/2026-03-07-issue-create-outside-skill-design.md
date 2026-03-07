# Issue-create syntax not discoverable outside add-issue skill

GitHub issue: https://github.com/elahti/deneb-marketplace/issues/85

## Problem

When Claude uses `issue-create` outside the `add-issue` skill (e.g., creating a side issue during `start-implementing-issue`), it has no documentation on the correct `--title`/`--body` flag syntax. It guesses positional args, which fail with an unhelpful error: `issue-create: unknown arg: Some title`.

An audit found 4 subcommands with the same pattern of unhelpful error messages on unknown or missing args: `issue-create`, `issue-close`, `project-list`, `project-field-list`.

## Decision

Improve error messages to include usage hints. No new flags, no positional arg shortcuts, no `--help` system.

Follow the existing good pattern from `cmd_set_status`:
```
set-status: unknown status 'X' (valid: todo, in-progress, done)
```

## Changes

### issue-create (cli.py, cmd_issue_create)

Unknown arg and missing-arg messages get a usage suffix:
```
issue-create: unknown arg: X. Usage: issue-create --title "..." --body "..." [--issue-type "..."]
issue-create: --title required. Usage: issue-create --title "..." --body "..." [--issue-type "..."]
issue-create: --body required. Usage: issue-create --title "..." --body "..." [--issue-type "..."]
```

### issue-close (cli.py, cmd_issue_close)

```
issue-close: unknown arg: X. Usage: issue-close <number> [--comment "..."]
```

### project-list (cli.py, cmd_project_list)

```
project-list: unknown arg: X. Usage: project-list --owner <owner>
project-list: --owner required. Usage: project-list --owner <owner>
```

### project-field-list (cli.py, cmd_project_field_list)

```
project-field-list: unknown arg: X. Usage: project-field-list <number> --owner <owner>
project-field-list: --owner required. Usage: project-field-list <number> --owner <owner>
project-field-list: project number required. Usage: project-field-list <number> --owner <owner>
```

## Testing

Update or add tests for each command to verify usage hints appear in error output for both unknown-arg and missing-arg cases.
