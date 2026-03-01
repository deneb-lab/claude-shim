#!/usr/bin/env bash
set -euo pipefail
HOOK_DIR="$(cd "$(dirname "$0")/../hook" && pwd)"
exec uv run --project "$HOOK_DIR" python -m github_project_tools "$@"
