import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from github_project_tools.cli import main


def make_config(tmp_path: Path) -> dict[str, object]:
    config_data: dict[str, object] = {
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
    return config_data


class TestReadConfig:
    def test_outputs_config_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["project"] == "https://github.com/users/testowner/projects/1"

    def test_missing_config_exits_1(self, tmp_path: Path) -> None:
        exit_code = main(["read-config"], cwd=tmp_path)
        assert exit_code == 1


class TestPreflight:
    def test_preflight_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["gh", "auth", "status"],
                returncode=0,
                stdout="",
                stderr="✓ Logged in\n  Token scopes: repo, project",
            )
            exit_code = main(["preflight"])

        assert exit_code == 0
        assert "OK" in capsys.readouterr().out
