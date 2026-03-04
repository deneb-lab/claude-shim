from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

CONFIG_FILENAME = ".claude-shim.json"
CONFIG_KEY = "github-project-tools"


class StatusMapping(BaseModel):
    name: str
    option_id: str = Field(alias="option-id")
    default: bool = False


class StatusField(BaseModel):
    id: str
    todo: StatusMapping | list[StatusMapping]
    in_progress: StatusMapping | list[StatusMapping] = Field(alias="in-progress")
    done: StatusMapping | list[StatusMapping]

    @model_validator(mode="after")
    def _check_list_defaults(self) -> StatusField:
        for key in ("todo", "in_progress", "done"):
            value: StatusMapping | list[StatusMapping] = getattr(self, key)
            if isinstance(value, list):
                defaults = [m for m in value if m.default]
                label = key.replace("_", "-")
                if len(defaults) != 1:
                    msg = (
                        f"Status list for '{label}' must have exactly one default, "
                        f"found {len(defaults)}"
                    )
                    raise ValueError(msg)
        return self

    def get_default(self, key: str) -> StatusMapping:
        """Return the default StatusMapping for a logical state."""
        attr = key.replace("-", "_")
        value = getattr(self, attr, None)
        if value is None:
            msg = f"Unknown status key: '{key}'"
            raise ValueError(msg)
        if isinstance(value, StatusMapping):
            return value
        defaults = [m for m in value if m.default]
        return defaults[0]


class ProjectFields(BaseModel):
    start_date: str = Field(alias="start-date")
    end_date: str = Field(alias="end-date")
    status: StatusField


class GitHubProjectToolsConfig(BaseModel):
    repo: str | None = None
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
