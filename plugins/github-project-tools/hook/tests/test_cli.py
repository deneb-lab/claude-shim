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

    def test_outputs_repo_when_present(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config_data: dict[str, object] = {
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

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["repo"] == "owner/my-repo"

    def test_outputs_null_repo_when_absent(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["repo"] is None

    def test_outputs_list_status_format(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config_data: dict[str, object] = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": "PVTF_start",
                    "end-date": "PVTF_end",
                    "status": {
                        "id": "PVTF_status",
                        "todo": {"name": "Todo", "option-id": "PVTO_1"},
                        "in-progress": {"name": "In Progress", "option-id": "PVTO_2"},
                        "done": [
                            {
                                "name": "Done",
                                "option-id": "PVTO_3",
                                "default": True,
                            },
                            {"name": "Arkisto", "option-id": "PVTO_4"},
                        ],
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        # Single object stays as object
        assert isinstance(output["fields"]["status"]["todo"], dict)
        # List stays as list
        assert isinstance(output["fields"]["status"]["done"], list)
        assert len(output["fields"]["status"]["done"]) == 2
        assert output["fields"]["status"]["done"][0]["option-id"] == "PVTO_3"
        assert output["fields"]["status"]["done"][0]["default"] is True
        assert output["fields"]["status"]["done"][1]["option-id"] == "PVTO_4"
        assert output["fields"]["status"]["done"][1]["default"] is False

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


class TestRepoDetection:
    def test_auto_detect_repo(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="owner/repo\n",
                    stderr="",
                ),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout='{"id":"I_1","number":1,"title":"Test","body":"","state":"OPEN"}',
                    stderr="",
                ),
            ]
            exit_code = main(["issue-view-full", "1"])
        assert exit_code == 0

    def test_repo_override_skips_detection(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout='{"id":"I_1"}', stderr=""
            )
            exit_code = main(["--repo", "other/repo", "issue-view-full", "1"])
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--repo" in call_args
        assert "other/repo" in call_args

    def test_auto_detect_fails_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="not a git repo"
            )
            with pytest.raises(SystemExit, match="1"):
                main(["issue-view-full", "1"])


class TestIssueView:
    def test_issue_view_passthrough(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="Issue #42: My issue\nBody text here",
                stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "issue-view", "42", "--web"])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Issue #42" in out
        call_args = mock_run.call_args[0][0]
        assert "issue" in call_args
        assert "view" in call_args
        assert "42" in call_args
        assert "--web" in call_args

    def test_issue_view_full(self, capsys: pytest.CaptureFixture[str]) -> None:
        json_output = (
            '{"id":"I_1","number":1,"title":"Test","body":"desc","state":"OPEN"}'
        )
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=json_output, stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "issue-view-full", "1"])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert json.loads(out)["state"] == "OPEN"


class TestIssueCreate:
    def test_create_with_title_and_body(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="https://github.com/owner/repo/issues/99\n",
                stderr="",
            )
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "My Title",
                    "--body",
                    "My Body",
                ]
            )
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--title" in call_args
        assert "My Title" in call_args
        assert "--body" in call_args
        assert "My Body" in call_args

    def test_create_with_label(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="https://github.com/owner/repo/issues/99\n",
                stderr="",
            )
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--label",
                    "bug",
                ]
            )
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--label" in call_args
        assert "bug" in call_args

    def test_create_missing_title_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--body", "B"])
        assert exit_code == 1
        assert "title" in capsys.readouterr().err.lower()

    def test_create_missing_body_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--title", "T"])
        assert exit_code == 1
        assert "body" in capsys.readouterr().err.lower()


class TestIssueAssign:
    def test_assigns_to_me(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="https://github.com/owner/repo/issues/42\n",
                stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "issue-assign", "42"])
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--add-assignee" in call_args
        assert "@me" in call_args


class TestIssueClose:
    def test_closes_open_issue(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="OPEN\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr=""
                ),
            ]
            exit_code = main(["--repo", "owner/repo", "issue-close", "42"])
        assert exit_code == 0
        # Second call should be the close command
        close_args = mock_run.call_args_list[1][0][0]
        assert "close" in close_args
        assert "--reason" in close_args
        assert "completed" in close_args

    def test_closes_with_comment(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="OPEN\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr=""
                ),
            ]
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-close",
                    "42",
                    "--comment",
                    "Done!",
                ]
            )
        assert exit_code == 0
        close_args = mock_run.call_args_list[1][0][0]
        assert "--comment" in close_args
        assert "Done!" in close_args

    def test_skips_close_for_closed_issue(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="CLOSED\n", stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "issue-close", "42"])
        assert exit_code == 0
        assert "already closed" in capsys.readouterr().err.lower()

    def test_closed_issue_with_comment_adds_comment(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="CLOSED\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr=""
                ),
            ]
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-close",
                    "42",
                    "--comment",
                    "Late comment",
                ]
            )
        assert exit_code == 0
        comment_args = mock_run.call_args_list[1][0][0]
        assert "comment" in comment_args
        assert "--body" in comment_args
        assert "Late comment" in comment_args

    def test_close_failure_returns_nonzero(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="OPEN\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="network error"
                ),
            ]
            exit_code = main(["--repo", "owner/repo", "issue-close", "42"])
        assert exit_code == 1
        assert "failed" in capsys.readouterr().err.lower()


# --- Helper function tests ---


class TestParseProjectUrl:
    def test_users_url(self) -> None:
        from github_project_tools.cli import parse_project_url

        owner, number = parse_project_url("https://github.com/users/elahti/projects/1")
        assert owner == "elahti"
        assert number == "1"

    def test_orgs_url(self) -> None:
        from github_project_tools.cli import parse_project_url

        owner, number = parse_project_url("https://github.com/orgs/my-org/projects/42")
        assert owner == "my-org"
        assert number == "42"

    def test_invalid_url_raises(self) -> None:
        from github_project_tools.cli import parse_project_url

        with pytest.raises(ValueError, match="Invalid project URL"):
            parse_project_url("https://github.com/elahti/repo")


class TestLoadConfigOrFail:
    def test_missing_config_exits(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="1"):
            main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
                cwd=tmp_path,
            )


class TestGraphql:
    def test_graphql_builds_correct_args(self) -> None:
        from github_project_tools.cli import graphql

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="{}", stderr=""
            )
            graphql("query { viewer { login } }", {"id": "123"})
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "api"
        assert call_args[1] == "graphql"
        assert "-f" in call_args
        assert "id=123" in call_args

    def test_graphql_with_jq_filter(self) -> None:
        from github_project_tools.cli import graphql

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="{}", stderr=""
            )
            graphql("query { viewer { login } }", {}, jq_filter=".data")
        call_args = mock_run.call_args[0][0]
        assert "--jq" in call_args
        assert ".data" in call_args


# --- Project board subcommand tests ---


class TestSetStatus:
    def test_uses_config_option_id(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            # First call: get_project_id
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        # Verify the option-id PVTO_3 (done) was used in the GraphQL call
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTO_3" in call_str

    def test_uses_in_progress_option_id(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "in-progress"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTO_2" in call_str

    def test_unknown_status_fails(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        exit_code = main(
            ["--repo", "owner/repo", "set-status", "PVTI_item", "invalid"],
            cwd=tmp_path,
        )
        assert exit_code == 1

    def test_uses_default_from_list_config(self, tmp_path: Path) -> None:
        config_data: dict[str, object] = {
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
                            {
                                "name": "Done",
                                "option-id": "PVTO_3",
                                "default": True,
                            },
                            {"name": "Arkisto", "option-id": "PVTO_4"},
                        ],
                    },
                },
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        # Should use PVTO_3 (the default), not PVTO_4
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTO_3" in call_str

    def test_uses_status_field_id(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "todo"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTF_status" in call_str


class TestSetDate:
    def test_sets_date_to_today(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        # Verify a date in YYYY-MM-DD format was passed
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        import re

        assert re.search(r"\d{4}-\d{2}-\d{2}", call_str)

    def test_sets_explicit_date(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout='{"data":{}}', stderr=""
                ),
            ]
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "set-date",
                    "PVTI_item",
                    "PVTF_start",
                    "2024-06-15",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "2024-06-15" in call_str


class TestGetProjectItem:
    def test_returns_item_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVTI_item123\n", stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-project-item", "I_node"], cwd=tmp_path
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "PVTI_item123" in out

    def test_uses_project_id_in_jq_filter(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVTI_item\n", stderr=""
                ),
            ]
            main(["--repo", "owner/repo", "get-project-item", "I_node"], cwd=tmp_path)
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVT_proj" in call_str


class TestGetStartDate:
    def test_returns_start_date(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout='{"item_id":"PVTI_x","date":"2024-01-15"}\n',
                    stderr="",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-start-date", "I_node"], cwd=tmp_path
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "PVTI_x" in out

    def test_uses_field_id_from_config(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr=""
                ),
            ]
            main(["--repo", "owner/repo", "get-start-date", "I_node"], cwd=tmp_path)
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        # Should use fieldValues (not fieldValueByName) and filter by config field ID
        assert "fieldValues" in call_str
        assert "PVTF_start" in call_str


class TestAddToProject:
    def test_returns_item_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVTI_new\n", stderr=""
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "add-to-project", "I_node"], cwd=tmp_path
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "PVTI_new" in out

    def test_passes_project_id_and_content_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVTI_new\n", stderr=""
                ),
            ]
            main(["--repo", "owner/repo", "add-to-project", "I_node"], cwd=tmp_path)
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "project=PVT_proj" in call_str
        assert "content=I_node" in call_str


class TestGetParent:
    def test_returns_parent(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"id":"I_parent","number":10,"title":"Parent","state":"OPEN"}\n',
                stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "get-parent", "I_child"])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "I_parent" in out

    def test_uses_jq_filter(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="{}\n", stderr=""
            )
            main(["--repo", "owner/repo", "get-parent", "I_child"])
        call_args = mock_run.call_args[0][0]
        assert "--jq" in call_args
        assert ".data.node.parent" in call_args


class TestCountOpenSubIssues:
    def test_counts_open(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="3\n", stderr=""
            )
            exit_code = main(
                ["--repo", "owner/repo", "count-open-sub-issues", "I_parent"]
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "3" in out

    def test_uses_correct_jq_filter(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="0\n", stderr=""
            )
            main(["--repo", "owner/repo", "count-open-sub-issues", "I_parent"])
        call_args = mock_run.call_args[0][0]
        assert "--jq" in call_args
        jq_idx = call_args.index("--jq")
        jq_filter = call_args[jq_idx + 1]
        assert "OPEN" in jq_filter
        assert "length" in jq_filter


class TestSetParent:
    def test_sets_parent(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="I_child\n", stderr=""
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-parent", "I_child", "I_parent"]
            )
        assert exit_code == 0

    def test_passes_correct_variables(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="I_child\n", stderr=""
            )
            main(["--repo", "owner/repo", "set-parent", "I_child", "I_parent"])
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        assert "parent=I_parent" in call_str
        assert "child=I_child" in call_str


# --- Discovery subcommand tests (setup skill) ---


class TestRepoDetect:
    def test_auto_detect_prints_repo(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="owner/repo\n", stderr=""
            )
            exit_code = main(["repo-detect"])
        assert exit_code == 0
        assert capsys.readouterr().out.strip() == "owner/repo"

    def test_repo_override(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "other/repo", "repo-detect"])
        assert exit_code == 0
        assert capsys.readouterr().out.strip() == "other/repo"

    def test_auto_detect_fails_exits_1(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="not a git repo"
            )
            with pytest.raises(SystemExit, match="1"):
                main(["repo-detect"])


class TestProjectList:
    def test_passes_owner_and_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        json_output = '{"projects":[{"number":1,"title":"My Project"}]}'
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=json_output, stderr=""
            )
            exit_code = main(["project-list", "--owner", "elahti"])
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "project" in call_args
        assert "list" in call_args
        assert "--owner" in call_args
        assert "elahti" in call_args
        assert "--format" in call_args
        assert "json" in call_args
        assert json_output in capsys.readouterr().out

    def test_missing_owner_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["project-list"])
        assert exit_code == 1
        assert "owner" in capsys.readouterr().err.lower()


class TestProjectFieldList:
    def test_passes_owner_number_and_format(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        json_output = (
            '{"fields":[{"name":"Status","id":"PVTF_1","type":"SINGLE_SELECT"}]}'
        )
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=json_output, stderr=""
            )
            exit_code = main(["project-field-list", "--owner", "elahti", "1"])
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "project" in call_args
        assert "field-list" in call_args
        assert "1" in call_args
        assert "--owner" in call_args
        assert "elahti" in call_args
        assert "--format" in call_args
        assert "json" in call_args
        assert json_output in capsys.readouterr().out

    def test_missing_owner_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["project-field-list", "1"])
        assert exit_code == 1
        assert "owner" in capsys.readouterr().err.lower()

    def test_missing_number_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["project-field-list", "--owner", "elahti"])
        assert exit_code == 1
        assert "number" in capsys.readouterr().err.lower()


class TestIssueGetAssignees:
    def test_returns_assignee_logins(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='["elahti","other-user"]\n',
                stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "issue-get-assignees", "42"])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "elahti" in out
        assert "other-user" in out
        call_args = mock_run.call_args[0][0]
        assert "issue" in call_args
        assert "view" in call_args
        assert "42" in call_args
        assert "assignees" in call_args

    def test_returns_empty_array_when_unassigned(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="[]\n",
                stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "issue-get-assignees", "42"])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "[]" in out


class TestGetStatusChangeDate:
    def test_returns_date_from_timeline(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                # get_project_id call
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                # GraphQL timeline query
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="2024-02-20\n",
                    stderr="",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-status-change-date", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out.strip()
        assert out == "2024-02-20"

    def test_returns_null_when_jq_returns_null(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                # jq "last" on empty array returns literal "null"
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="null\n",
                    stderr="",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-status-change-date", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out.strip()
        assert out == "null"

    def test_returns_null_when_no_events(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                # get_project_id call
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                # GraphQL timeline query — no matching events
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="",
                    stderr="",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "get-status-change-date", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out.strip()
        assert out == "null"


class TestIssueList:
    def test_passthrough_args(self, capsys: pytest.CaptureFixture[str]) -> None:
        json_output = '[{"number":1,"projectItems":[]}]'
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=json_output, stderr=""
            )
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-list",
                    "--limit",
                    "5",
                    "--json",
                    "number,projectItems",
                ]
            )
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "issue" in call_args
        assert "list" in call_args
        assert "--repo" in call_args
        assert "owner/repo" in call_args
        assert "--limit" in call_args
        assert "5" in call_args
        assert "--json" in call_args
        assert "number,projectItems" in call_args
        assert json_output in capsys.readouterr().out
