from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

CONFIG_FILENAME = ".claude-shim.json"


class QualityCheckEntry(BaseModel):
    pattern: str
    commands: list[str]


class QualityChecks(BaseModel):
    include: list[QualityCheckEntry]
    exclude: list[str] = []


class ClaudeShimConfig(BaseModel):
    quality_checks: QualityChecks = Field(alias="quality-checks")


def load_config(cwd: Path) -> ClaudeShimConfig | None:
    config_path = cwd / CONFIG_FILENAME
    if not config_path.exists():
        return None

    raw = json.loads(config_path.read_text())

    if "quality-checks" not in raw:
        return None

    try:
        return ClaudeShimConfig.model_validate(raw)
    except ValidationError as exc:
        msg = f"Invalid {CONFIG_FILENAME}: {exc}"
        raise ValueError(msg) from exc
