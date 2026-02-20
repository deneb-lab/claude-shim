# Claude Code Hooks Plugin Design

## Problem

Claude Code users need a way to automatically run quality checks (formatting, linting, auto-fix) on files after Claude edits them. The existing reference implementation in the deneb repo uses Bun + TypeScript with hardcoded file-type checks. We need a config-driven, zero-setup alternative that can be redistributed as a marketplace plugin.

## Requirements

- Zero-setup hook redistributable via the claude-shim marketplace
- Python + uv managed project: uv installs Python and all deps automatically on first invocation
- Fail-closed when uv is not available (command fails, stderr shown to Claude)
- Config-driven via `.claude-shim.json` at the root of the consuming repo
- Glob pattern matching with brace expansion (`{ts,tsx}`) and `**` recursion
- Multiple patterns can match the same file; commands execute in config order
- Sequential command execution within each pattern entry
- Block on first command failure, feeding error output back to Claude
- Exclude patterns to skip files (e.g., `node_modules`, generated code)

## Design

### Plugin Structure

```
plugins/claude-code-hooks/
├── .claude-plugin/plugin.json          # plugin metadata
├── hooks/hooks.json                    # native PostToolUse hook registration
└── hook/                               # uv-managed Python project
    ├── pyproject.toml
    ├── uv.lock
    ├── src/claude_code_hooks/
    │   ├── __init__.py
    │   ├── main.py                     # entry point: stdin → dispatch → stdout/stderr
    │   ├── config.py                   # Pydantic models + .claude-shim.json loader
    │   ├── matcher.py                  # glob matching with exclude/include logic
    │   └── runner.py                   # sequential command execution
    └── tests/
        ├── __init__.py
        ├── test_config.py
        ├── test_matcher.py
        ├── test_runner.py
        └── test_main.py
```

### Hook Registration

The plugin uses Claude Code's native plugin hook mechanism via `hooks/hooks.json`. When users enable the plugin, the PostToolUse hook is automatically merged into their session. No setup skill needed.

```json
{
  "description": "Config-driven quality checks for edited files",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --project \"${CLAUDE_PLUGIN_ROOT}/hook\" python -m claude_code_hooks.main",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

- `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's cached directory
- `uv run --project` handles Python installation and dependency resolution
- If `uv` is not on PATH, the command fails and stderr is shown to Claude (fail-closed)

### Config Format (`.claude-shim.json`)

The config file lives at the root of the consuming repo. The `quality-checks` key is namespaced to allow future config sections.

```json
{
  "quality-checks": {
    "include": [
      {
        "pattern": "**/*.{js,jsx,ts,tsx}",
        "commands": [
          "npx prettier --write",
          "npx eslint --fix"
        ]
      },
      {
        "pattern": "**/*.{ts,tsx}",
        "commands": [
          "npx eslint"
        ]
      }
    ],
    "exclude": [
      "node_modules",
      "src/generated/**/*.ts"
    ]
  }
}
```

**Execution for a `.tsx` file:** both include entries match, so commands run in order: `npx prettier --write <file>`, `npx eslint --fix <file>`, `npx eslint <file>`.

**Execution for a `.js` file:** only the first entry matches: `npx prettier --write <file>`, `npx eslint --fix <file>`.

### Data Flow

```
Claude writes/edits file
  → Claude Code fires PostToolUse with JSON on stdin
  → main.py reads stdin, extracts file_path from tool_input and cwd
  → config.py loads {cwd}/.claude-shim.json, validates via Pydantic
  → matcher.py checks file against exclude patterns, then collects
    all matching include entries in config order
  → runner.py runs each command sequentially, appending file_path as last arg
  → main.py returns result to stdout (or exits 2 with stderr on failure)
```

### Python Modules

**`main.py`** — Entry point. Reads JSON from stdin, extracts `file_path` from `tool_input` and `cwd` from the payload. If no `.claude-shim.json` exists, exits 0 silently. Orchestrates config loading, matching, and command execution.

**`config.py`** — Pydantic models:

```python
class QualityCheckEntry(BaseModel):
    pattern: str
    commands: list[str]

class QualityChecks(BaseModel):
    include: list[QualityCheckEntry]
    exclude: list[str] = []

class ClaudeShimConfig(BaseModel):
    quality_checks: QualityChecks = Field(alias="quality-checks")
```

Returns `None` if the `quality-checks` key is absent.

**`matcher.py`** — Takes a file path (relative to cwd), exclude list, and include list. Uses `wcmatch.glob` for brace expansion and `**` support. Returns an ordered list of commands from all matching entries.

**`runner.py`** — Executes commands sequentially via `subprocess.run`. Each command gets the absolute file path appended as the last argument. Stops on first failure and returns the command name + its output.

### Response Behavior

| Scenario | Exit code | Output |
|:--|:--|:--|
| All commands pass | 0 | Empty JSON `{}` (silent) |
| A command fails | 2 | stderr: command name + output |
| No config file | 0 | Empty JSON (nothing to check) |
| No patterns match | 0 | Empty JSON (file type not covered) |
| Config parse error | 2 | stderr: validation error |

### Project Configuration

The uv project uses latest versions of all dependencies:

**Runtime dependencies:** `pydantic`, `wcmatch`

**Dev dependencies:** `ruff`, `pyright`, `pytest`

**Tooling:** ruff with comprehensive lint rules (B, C4, COM, E, F, I, PERF, RUF, SIM, UP, W), pyright in strict mode, pytest for unit tests.

### CI Integration

**Docker image update** (`.github/images/ci/Dockerfile`): add `uv` installation.

**New CI jobs** in `.github/workflows/ci.yml`:

- `python-lint`: `ruff check` + `ruff format --check`
- `python-typecheck`: `pyright`
- `python-test`: `pytest`

All run via `uv run --project plugins/claude-code-hooks/hook` so uv handles Python + deps automatically.

### Testing Strategy

- `test_config.py`: valid/invalid config parsing, missing keys, empty include
- `test_matcher.py`: single pattern, brace expansion, multiple matching patterns, exclude filtering, path relativization
- `test_runner.py`: successful/failed commands, sequential stop on failure, file path appending, timeout handling
- `test_main.py`: full stdin-to-stdout integration flow with mocked subprocess

### Modified Existing Files

- `.claude-plugin/marketplace.json`: add `claude-code-hooks` plugin entry
- `.github/workflows/ci.yml`: add Python CI jobs
- `.github/images/ci/Dockerfile`: add uv
- `README.md`: add plugin listing

## Decisions

- **Python + uv over TypeScript + Bun**: zero-setup for users (uv auto-installs Python), no runtime dependency on Bun/Node
- **Native plugin hooks over setup skill**: `hooks/hooks.json` is automatically merged when the plugin is enabled, no manual configuration needed
- **wcmatch over stdlib fnmatch**: fnmatch lacks brace expansion (`{ts,tsx}`) which is essential for the config format
- **Pydantic over manual parsing**: clear validation errors, type safety, extensible for future config sections
- **Config-driven over hardcoded**: users define their own tools and patterns per repo instead of the hook deciding what to run
