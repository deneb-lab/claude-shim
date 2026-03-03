# Remove JSON Schema Feature

## Context

The JSON schema feature (`claude-shim.schema.json`) was generated from Pydantic models in the quality-check-hook plugin and provided IDE autocompletion for `.claude-shim.json`. It only covered `quality-checks` — the `github-project-tools` section was never included. The feature is being removed to reduce maintenance overhead.

## Changes

### Delete
- `plugins/quality-check-hook/claude-shim.schema.json` — generated schema file
- `plugins/quality-check-hook/hook/scripts/generate_schema.py` — generator script

### Edit
- `.claude-shim.json` — remove `$schema` line
- `plugins/quality-check-hook/skills/setup-quality-check-hook/SKILL.md` — remove `$schema` from Step 6 example config
- `plugins/quality-check-hook/CLAUDE.md` — remove JSON Schema section and `generate_schema.py` from architecture
- `README.md` — remove `$schema` from example config
- `plugins/quality-check-hook/hook/tests/test_config.py` — remove `test_schema_key_ignored()` test
- `plugins/github-project-tools/hook/tests/test_config.py` — remove `$schema` from `test_extra_keys_ignored()` test data
- `docs/plans/2026-02-28-configurable-github-project-skills.md` — remove `$schema` from sample config

### No change
- `renovate.json` — its `$schema` is for Renovate, unrelated
- Python config models — no `$schema`-specific code
- Setup skills — passive removal, `$schema` simply stops being written
