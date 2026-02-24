"""Generate JSON Schema for .claude-shim.json from Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from quality_check_hook.config import ClaudeShimConfig

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "claude-shim.schema.json"


def main() -> None:
    schema = ClaudeShimConfig.model_json_schema(
        mode="validation",
        by_alias=True,
    )

    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = (
        "https://raw.githubusercontent.com/elahti/claude-shim/main/plugins/quality-check-hook/claude-shim.schema.json"
    )

    # Add top-level properties description
    if "properties" in schema and "quality-checks" in schema["properties"]:
        schema["properties"]["quality-checks"]["description"] = (
            "Quality check rules — which files to match and which commands to run"
        )

    # Allow $schema key in the config file
    schema["properties"]["$schema"] = {
        "type": "string",
        "description": "JSON Schema reference for editor validation",
    }

    SCHEMA_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Schema written to {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
