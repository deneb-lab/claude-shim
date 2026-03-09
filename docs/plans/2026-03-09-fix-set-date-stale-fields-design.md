# Fix set-date stale field IDs

## Problem

The `set-date` subcommand fails with "Did not receive a number value to update a field of type number" when field IDs in `.claude-shim.json` become stale after project board reconfiguration. The error is confusing and gives no guidance on how to fix it.

## Approach

Store field type metadata alongside field IDs in config. Validate before the GraphQL mutation. Add a hint on any failure.

Not backward compatible with older plugin versions — accepted trade-off.

## Config schema change

Date fields change from plain strings to objects:

```json
// Old format:
"start-date": "PVTF_xxx"

// New format:
"start-date": {"id": "PVTF_xxx", "type": "DATE"}
```

Backward compat for old configs: Pydantic validator normalizes plain strings to `{"id": "<value>", "type": null}`.

## Pre-validation in cmd_set_date

Before the GraphQL mutation, check field type metadata. If type is present and not `"DATE"`, return error:

```
set-date: field PVTF_xxx has type NUMBER, expected DATE. Re-run github-project-tools:setup-github-project-tools to refresh field IDs.
```

If type is `null` (old config), skip validation.

## Failure hint

On any `set-date` GraphQL failure, append:

```
Hint: if field IDs are stale, re-run github-project-tools:setup-github-project-tools to refresh them.
```

## Setup skill update

When writing config, store `{"id": "PVTF_xxx", "type": "DATE"}` instead of the plain ID string. The setup skill already knows which fields are date fields from name matching — no extra API call needed.

## Verification

`project-field-list` output does NOT distinguish date fields from other `ProjectV2Field` types. However, the GraphQL API does expose `dataType: "DATE"` on field nodes. The setup skill's name matching is sufficient — when it picks "Start date", it knows the type is DATE.

## Files changed

1. `config.py` — `ProjectFields`: date fields accept `str | DateField`, validator normalizes strings
2. `cli.py` — `cmd_set_date`: pre-validation + failure hint on mutation error
3. `cli.py` — `cmd_read_config`: output full object (skills extract `.id`)
4. Setup skill `SKILL.md` — write `{"id", "type"}` objects instead of plain strings
5. Tests — old config compat, new config validation, stale type error, mutation failure hint
