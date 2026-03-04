import json
from pathlib import Path

import pytest

from github_project_tools.config import StatusField, StatusMapping, load_config


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
        assert isinstance(result.fields.status.todo, StatusMapping)
        assert result.fields.status.todo.name == "Todo"
        assert result.fields.status.todo.option_id == "PVTO_1"
        assert isinstance(result.fields.status.in_progress, StatusMapping)
        assert result.fields.status.in_progress.name == "In Progress"
        assert result.fields.status.in_progress.option_id == "PVTO_2"
        assert isinstance(result.fields.status.done, StatusMapping)
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

    def test_status_mapping_default_field(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {
                            "name": "Todo",
                            "option-id": "PVTO_1",
                            "default": True,
                        },
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
        assert isinstance(result.fields.status.todo, StatusMapping)
        assert result.fields.status.todo.default is True
        assert isinstance(result.fields.status.in_progress, StatusMapping)
        assert result.fields.status.in_progress.default is False
        assert isinstance(result.fields.status.done, StatusMapping)
        assert result.fields.status.done.default is False

    def test_status_as_list_with_single_item(self, tmp_path: Path) -> None:
        config_data = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": [
                            {"name": "Todo", "option-id": "PVTO_1", "default": True}
                        ],
                        "in-progress": [
                            {
                                "name": "In Progress",
                                "option-id": "PVTO_2",
                                "default": True,
                            }
                        ],
                        "done": [
                            {"name": "Done", "option-id": "PVTO_3", "default": True}
                        ],
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert isinstance(result.fields.status.todo, list)
        assert len(result.fields.status.todo) == 1
        assert result.fields.status.todo[0].name == "Todo"
        assert result.fields.status.todo[0].option_id == "PVTO_1"
        assert result.fields.status.todo[0].default is True

    def test_status_as_list_with_multiple_items(self, tmp_path: Path) -> None:
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
                        "done": [
                            {
                                "name": "Done",
                                "option-id": "PVTO_3",
                                "default": True,
                            },
                            {
                                "name": "Arkisto",
                                "option-id": "PVTO_4",
                            },
                        ],
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert isinstance(result.fields.status.done, list)
        assert len(result.fields.status.done) == 2
        assert result.fields.status.done[0].name == "Done"
        assert result.fields.status.done[0].default is True
        assert result.fields.status.done[1].name == "Arkisto"
        assert result.fields.status.done[1].default is False

    def test_status_list_without_default_raises(self, tmp_path: Path) -> None:
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
                        "done": [
                            {"name": "Done", "option-id": "PVTO_3"},
                            {"name": "Arkisto", "option-id": "PVTO_4"},
                        ],
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_status_list_with_multiple_defaults_raises(self, tmp_path: Path) -> None:
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
                        "done": [
                            {
                                "name": "Done",
                                "option-id": "PVTO_3",
                                "default": True,
                            },
                            {
                                "name": "Arkisto",
                                "option-id": "PVTO_4",
                                "default": True,
                            },
                        ],
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError):
            load_config(tmp_path)


class TestStatusFieldGetDefault:
    def test_get_default_single_object(self) -> None:
        field = StatusField.model_validate(
            {
                "id": "F1",
                "todo": {"name": "Todo", "option-id": "O1"},
                "in-progress": {"name": "In Progress", "option-id": "O2"},
                "done": {"name": "Done", "option-id": "O3"},
            }
        )
        result = field.get_default("todo")
        assert result.option_id == "O1"

    def test_get_default_list(self) -> None:
        field = StatusField.model_validate(
            {
                "id": "F1",
                "todo": {"name": "Todo", "option-id": "O1"},
                "in-progress": {"name": "In Progress", "option-id": "O2"},
                "done": [
                    {"name": "Done", "option-id": "O3", "default": True},
                    {"name": "Arkisto", "option-id": "O4"},
                ],
            }
        )
        result = field.get_default("done")
        assert result.option_id == "O3"
        assert result.name == "Done"

    def test_get_default_in_progress_with_hyphen(self) -> None:
        field = StatusField.model_validate(
            {
                "id": "F1",
                "todo": {"name": "Todo", "option-id": "O1"},
                "in-progress": [
                    {"name": "In Progress", "option-id": "O2", "default": True},
                    {"name": "Active", "option-id": "O5"},
                ],
                "done": {"name": "Done", "option-id": "O3"},
            }
        )
        result = field.get_default("in-progress")
        assert result.option_id == "O2"

    def test_get_default_unknown_key_raises(self) -> None:
        field = StatusField.model_validate(
            {
                "id": "F1",
                "todo": {"name": "Todo", "option-id": "O1"},
                "in-progress": {"name": "In Progress", "option-id": "O2"},
                "done": {"name": "Done", "option-id": "O3"},
            }
        )
        with pytest.raises(ValueError, match="Unknown status key"):
            field.get_default("invalid")
