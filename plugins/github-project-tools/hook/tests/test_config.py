import json
from pathlib import Path

import pytest

from github_project_tools.config import load_config


class TestGitHubProjectToolsConfig:
    def test_valid_config(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.project == "https://github.com/users/testowner/projects/1"
        assert result.fields.start_date == "PVTF_start"
        assert result.fields.end_date == "PVTF_end"
        assert result.fields.status.id == "PVTF_status"
        assert result.fields.status.todo.name == "Todo"
        assert result.fields.status.todo.option_id == "PVTO_1"
        assert result.fields.status.in_progress.name == "In Progress"
        assert result.fields.status.in_progress.option_id == "PVTO_2"
        assert result.fields.status.done.name == "Done"
        assert result.fields.status.done.option_id == "PVTO_3"

    def test_no_config_file_returns_none(self, tmp_path: Path) -> None:
        result = load_config(tmp_path)
        assert result is None

    def test_no_github_project_tools_key_returns_none(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps({"quality-checks": {"include": []}}))

        result = load_config(tmp_path)
        assert result is None

    def test_invalid_config_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps({"github-project-tools": {"project": 123}}))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_missing_status_role_raises(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_extra_keys_ignored(self, tmp_path: Path) -> None:
        config_data: dict[str, object] = {
            "quality-checks": {"include": []},
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                },
            },
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)
        assert result is not None
        assert result.project == "https://github.com/users/testowner/projects/1"

    def test_config_with_repo(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "repo": "owner/my-repo",
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.repo == "owner/my-repo"

    def test_config_without_repo_returns_none_repo(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {
                            "name": "In Progress",
                            "option-id": "PVTO_2",
                        },
                        "done": {"name": "Done", "option-id": "PVTO_3"},
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.repo is None
