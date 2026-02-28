from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

CONFIG_FILENAME = ".claude-shim.json"
CONFIG_KEY = "github-project-tools"


class StatusMapping(BaseModel):
    name: str
    option_id: str = Field(alias="option-id")


class StatusField(BaseModel):
    id: str
    todo: StatusMapping
    in_progress: StatusMapping = Field(alias="in-progress")
    done: StatusMapping


class ProjectFields(BaseModel):
    start_date: str = Field(alias="start-date")
    end_date: str = Field(alias="end-date")
    status: StatusField


class GitHubProjectToolsConfig(BaseModel):
    project: str
    fields: ProjectFields


def load_config(cwd: Path) -> GitHubProjectToolsConfig | None:
    config_path = cwd / CONFIG_FILENAME
    if not config_path.exists():
        return None

    raw = json.loads(config_path.read_text())

    if CONFIG_KEY not in raw:
        return None

    try:
        return GitHubProjectToolsConfig.model_validate(raw[CONFIG_KEY])
    except ValidationError as exc:
        msg = f"Invalid {CONFIG_FILENAME}: {exc}"
        raise ValueError(msg) from exc
