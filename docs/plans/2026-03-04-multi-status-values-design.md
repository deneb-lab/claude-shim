# Support Multiple Status Values for Logical States

Issue: [#79](https://github.com/elahti/deneb-marketplace/issues/79)

## Problem

GitHub project skills only support one status value per logical state (todo, in-progress, done). Users need multiple status options per state — e.g., both "Done" and "Arkisto" mapping to the `done` logical state — to support future mass-update operations that can target specific states without affecting others.

## Approach: Union Type in Pydantic

Accept either a single `StatusMapping` object (backwards compat) or a list of `StatusMapping` objects in `.claude-shim.json`. The CLI normalizes internally and uses the item marked `default: true`.

## Config Format

**Single object (backwards compat only — setup no longer writes this format):**

```json
"todo": { "name": "Todo", "option-id": "f75ad846" }
```

**List (canonical format — setup always writes this):**

```json
"done": [
  { "name": "Done", "option-id": "98236657", "default": true },
  { "name": "Arkisto", "option-id": "123456" }
]
```

Rules:
- Single object: treated as the only (and default) mapping. `default` field optional.
- List: exactly one item must have `"default": true`.

## Pydantic Models (`config.py`)

`StatusMapping` gains an optional `default` field:

```python
class StatusMapping(BaseModel):
    name: str
    option_id: str = Field(alias="option-id")
    default: bool = False
```

`StatusField` uses union types:

```python
class StatusField(BaseModel):
    id: str
    todo: StatusMapping | list[StatusMapping]
    in_progress: StatusMapping | list[StatusMapping] = Field(alias="in-progress")
    done: StatusMapping | list[StatusMapping]
```

A `get_default(key)` helper method returns the default `StatusMapping` for a given logical state. For single objects, returns the object directly. For lists, returns the item with `default=True`, raising `ValueError` if not exactly one.

A model validator ensures each list-type field has exactly one default.

## CLI Changes (`cli.py`)

`cmd_set_status` uses `config.fields.status.get_default(status_key)` instead of direct attribute access. Interface unchanged: `set-status <item_id> <status_key>`.

## Setup Skill Changes

**Step 5 (Detect Status Mappings):**

For each logical state:
1. Auto-match candidates from options using existing name patterns.
2. Present all options with `AskUserQuestion` multi-select, pre-selecting matches.
3. If multiple selected, ask which is the default.
4. Always write as list format (even for single selections — single item gets `"default": true`).

## Skills (add-issue, start-implementation, end-implementation)

No changes. They call `set-status` with `todo`/`in-progress`/`done` — the CLI resolves the default.

## Testing

Extend existing test files:
- `test_config.py`: Single-object compat, single-item list, multi-item list, validation failures (no default, multiple defaults).
- `test_cli.py`: `cmd_set_status` with both config formats.
