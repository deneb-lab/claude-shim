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


def make_config_with_issue_types(tmp_path: Path) -> dict[str, object]:
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
                "issue-types": [
                    {"name": "Epic", "id": "IT_epic", "default": True},
                    {"name": "Task", "id": "IT_task"},
                    {"name": "Bug", "id": "IT_bug"},
                ],
            },
        }
    }
    config_file = tmp_path / ".claude-shim.json"
    config_file.write_text(json.dumps(config_data))
    return config_data


def make_config_new_date_format(tmp_path: Path) -> dict[str, object]:
    config_data: dict[str, object] = {
        "github-project-tools": {
            "project": "https://github.com/users/testowner/projects/1",
            "fields": {
                "start-date": {"id": "PVTF_start", "type": "DATE"},
                "end-date": {"id": "PVTF_end", "type": "DATE"},
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

    def test_outputs_issue_types_when_present(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert "issue-types" in output["fields"]
        types = output["fields"]["issue-types"]
        assert len(types) == 3
        assert types[0]["name"] == "Epic"
        assert types[0]["default"] is True

    def test_outputs_null_issue_types_when_absent(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)

        exit_code = main(["read-config"], cwd=tmp_path)

        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["fields"]["issue-types"] is None

    def test_new_date_format_parses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_new_date_format(tmp_path)
        exit_code = main(["read-config"], cwd=tmp_path)
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["fields"]["start-date"] == {"id": "PVTF_start", "type": "DATE"}
        assert out["fields"]["end-date"] == {"id": "PVTF_end", "type": "DATE"}

    def test_old_string_format_normalizes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        exit_code = main(["read-config"], cwd=tmp_path)
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["fields"]["start-date"] == {"id": "PVTF_start", "type": None}
        assert out["fields"]["end-date"] == {"id": "PVTF_end", "type": None}


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
    def test_auto_detect_repo(self) -> None:
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


class TestDispatchArgValidation:
    def test_1_arg_subcommand_missing_arg(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["issue-view"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "missing required arguments" in err
        assert "Usage: issue-view" in err

    def test_2_arg_subcommand_missing_all_args(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["set-parent"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "missing required arguments" in err
        assert "Usage: set-parent" in err

    def test_2_arg_subcommand_missing_second_arg(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["set-parent", "I_child"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "missing required arguments" in err
        assert "Usage: set-parent" in err


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

    def test_create_gh_failure_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="label 'task' not found",
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
                ]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-create" in err
        assert "label 'task' not found" in err

    def test_create_rejects_label_flag(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
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
        assert exit_code == 1
        assert "unknown arg" in capsys.readouterr().err.lower()

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

    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                ["--repo", "owner/repo", "issue-create", "Some title", "--body", "B"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-create --title" in err

    def test_missing_title_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--body", "B"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-create --title" in err

    def test_missing_body_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--title", "T"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-create --title" in err

    def test_title_flag_without_value_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-create", "--title"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "--title requires an argument" in err

    def test_body_flag_without_value_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                ["--repo", "owner/repo", "issue-create", "--title", "T", "--body"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "--body requires an argument" in err

    def test_issue_type_flag_without_value_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--issue-type",
                ]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "--issue-type requires an argument" in err

    def test_create_with_issue_type(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)
        call_count = 0

        def mock_side_effect(
            args: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # gh issue create
                return subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="https://github.com/owner/repo/issues/42\n",
                    stderr="",
                )
            if call_count == 2:
                # gh issue view (get node ID)
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="I_node42\n", stderr=""
                )
            # graphql mutation (set type)
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

        with patch("github_project_tools.cli.run_gh", side_effect=mock_side_effect):
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "My Title",
                    "--body",
                    "My Body",
                    "--issue-type",
                    "Epic",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "https://github.com/owner/repo/issues/42" in out

    def test_create_with_issue_type_case_insensitive(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)

        def mock_side_effect(
            args: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="https://github.com/owner/repo/issues/42\n",
                stderr="",
            )

        with patch("github_project_tools.cli.run_gh", side_effect=mock_side_effect):
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--issue-type",
                    "epic",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0

    def test_create_with_issue_type_calls_update_mutation(self, tmp_path: Path) -> None:
        make_config_with_issue_types(tmp_path)
        calls: list[list[str]] = []

        def mock_side_effect(
            args: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            if len(calls) == 1:
                return subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="https://github.com/owner/repo/issues/42\n",
                    stderr="",
                )
            if len(calls) == 2:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="I_node42\n", stderr=""
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

        with patch("github_project_tools.cli.run_gh", side_effect=mock_side_effect):
            main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--issue-type",
                    "Task",
                ],
                cwd=tmp_path,
            )
        # Third call should be the GraphQL mutation
        assert len(calls) == 3
        mutation_args = " ".join(calls[2])
        assert "id=I_node42" in mutation_args
        assert "typeId=IT_task" in mutation_args

    def test_create_with_unknown_issue_type_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config_with_issue_types(tmp_path)
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--issue-type",
                    "NonExistent",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "unknown issue type" in err.lower()

    def test_create_with_issue_type_no_config_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # tmp_path has no .claude-shim.json
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-create",
                    "--title",
                    "T",
                    "--body",
                    "B",
                    "--issue-type",
                    "Epic",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-type" in err.lower()

    def test_create_without_issue_type_still_works(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Backward compat: no --issue-type means no config needed, no extra calls."""
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
                ]
            )
        assert exit_code == 0
        # Only one call (gh issue create), no node ID or mutation calls
        assert mock_run.call_count == 1


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

    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                ["--repo", "owner/repo", "issue-close", "42", "--label", "bug"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-close <number> [--comment" in err

    def test_comment_flag_without_value_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-close", "42", "--comment"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "--comment requires an argument" in err


class TestIssueComment:
    def test_posts_comment(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-comment",
                    "42",
                    "--body",
                    "Hello world",
                ]
            )
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "issue" in call_args
        assert "comment" in call_args
        assert "42" in call_args
        assert "--body" in call_args
        assert "Hello world" in call_args

    def test_failure_returns_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="network error"
            )
            exit_code = main(
                [
                    "--repo",
                    "owner/repo",
                    "issue-comment",
                    "42",
                    "--body",
                    "Hello",
                ]
            )
        assert exit_code == 1
        assert "failed" in capsys.readouterr().err.lower()

    def test_body_required(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-comment", "42"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "--body required" in err

    def test_body_flag_without_value_exits_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-comment", "42", "--body"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "--body requires an argument" in err

    def test_unknown_arg_shows_usage(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(
                ["--repo", "owner/repo", "issue-comment", "42", "--label", "bug"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: issue-comment" in err

    def test_missing_number_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh"):
            exit_code = main(["--repo", "owner/repo", "issue-comment"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "missing required arguments" in err


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
            parse_project_url("https://github.com/deneb-lab/repo")


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

    def test_rejects_non_date_field_type(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        config_data: dict[str, object] = {
            "github-project-tools": {
                "project": "https://github.com/users/testowner/projects/1",
                "fields": {
                    "start-date": {"id": "PVTF_start", "type": "NUMBER"},
                    "end-date": {"id": "PVTF_end", "type": "DATE"},
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
        (tmp_path / ".claude-shim.json").write_text(json.dumps(config_data))
        exit_code = main(
            ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
            cwd=tmp_path,
        )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "NUMBER" in err
        assert "expected DATE" in err
        assert "setup-github-project-tools" in err

    def test_skips_validation_when_type_is_null(self, tmp_path: Path) -> None:
        make_config(tmp_path)  # old format — type will be None after normalization
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

    def test_failure_includes_hint(
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
                    returncode=1,
                    stdout="",
                    stderr="Did not receive a number value",
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-date", "PVTI_item", "PVTF_start"],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "setup-github-project-tools" in err


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
            exit_code = main(["project-list", "--owner", "deneb-lab"])
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "project" in call_args
        assert "list" in call_args
        assert "--owner" in call_args
        assert "deneb-lab" in call_args
        assert "--format" in call_args
        assert "json" in call_args
        assert json_output in capsys.readouterr().out

    def test_missing_owner_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["project-list"])
        assert exit_code == 1
        assert "owner" in capsys.readouterr().err.lower()

    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-list", "unexpected"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-list --owner <owner>" in err

    def test_missing_owner_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-list"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-list --owner <owner>" in err


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
            exit_code = main(["project-field-list", "--owner", "deneb-lab", "1"])
        assert exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "project" in call_args
        assert "field-list" in call_args
        assert "1" in call_args
        assert "--owner" in call_args
        assert "deneb-lab" in call_args
        assert "--format" in call_args
        assert "json" in call_args
        assert json_output in capsys.readouterr().out

    def test_missing_owner_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["project-field-list", "1"])
        assert exit_code == 1
        assert "owner" in capsys.readouterr().err.lower()

    def test_missing_number_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["project-field-list", "--owner", "deneb-lab"])
        assert exit_code == 1
        assert "number" in capsys.readouterr().err.lower()

    def test_unknown_arg_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-field-list", "--owner", "deneb-lab", "--bad"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-field-list <number> --owner <owner>" in err

    def test_missing_owner_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-field-list", "1"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-field-list <number> --owner <owner>" in err

    def test_missing_number_shows_usage_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["project-field-list", "--owner", "deneb-lab"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Usage: project-field-list <number> --owner <owner>" in err


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


class TestListSubIssues:
    def test_returns_sub_issues(self, capsys: pytest.CaptureFixture[str]) -> None:
        sub_issues_json = json.dumps(
            [
                {"id": "I_sub1", "number": 10, "title": "Sub 1", "state": "OPEN"},
                {"id": "I_sub2", "number": 11, "title": "Sub 2", "state": "CLOSED"},
            ]
        )
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=sub_issues_json + "\n", stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "list-sub-issues", "I_parent"])
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2
        assert out[0]["id"] == "I_sub1"
        assert out[1]["state"] == "CLOSED"

    def test_returns_empty_array_when_no_sub_issues(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            exit_code = main(["--repo", "owner/repo", "list-sub-issues", "I_parent"])
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert out == []

    def test_uses_correct_jq_filter(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["--repo", "owner/repo", "list-sub-issues", "I_parent"])
        call_args = mock_run.call_args[0][0]
        assert "--jq" in call_args
        jq_idx = call_args.index("--jq")
        jq_filter = call_args[jq_idx + 1]
        assert "subIssues" in jq_filter


class TestListStatusOptions:
    def test_returns_status_options(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        options_json = json.dumps(
            [
                {"id": "OPT_1", "name": "Todo"},
                {"id": "OPT_2", "name": "In Progress"},
                {"id": "OPT_3", "name": "Done"},
                {"id": "OPT_4", "name": "Blocked"},
            ]
        )
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=options_json + "\n", stderr=""
            )
            exit_code = main(["list-status-options"], cwd=tmp_path)
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 4
        assert out[3]["name"] == "Blocked"

    def test_queries_status_field_id_from_config(self, tmp_path: Path) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["list-status-options"], cwd=tmp_path)
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        # Should use the status field ID from config
        assert "PVTF_status" in call_str

    def test_missing_config_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="1"):
            main(["list-status-options"], cwd=tmp_path)


class TestSetStatusByOptionId:
    def test_sets_status_with_raw_option_id(self, tmp_path: Path) -> None:
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
                    "set-status-by-option-id",
                    "PVTI_item",
                    "OPT_custom",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        # Verify the raw option ID was used in the GraphQL call
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "OPT_custom" in call_str

    def test_uses_status_field_id_from_config(self, tmp_path: Path) -> None:
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
                    "set-status-by-option-id",
                    "PVTI_item",
                    "OPT_1",
                ],
                cwd=tmp_path,
            )
        assert exit_code == 0
        graphql_call = mock_run.call_args_list[1]
        call_str = " ".join(graphql_call[0][0])
        assert "PVTF_status" in call_str


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


class TestListIssueTypes:
    def test_returns_issue_types(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='[{"id":"IT_1","name":"Epic","description":""},{"id":"IT_2","name":"Task","description":""}]\n',
                stderr="",
            )
            exit_code = main(["--repo", "owner/repo", "list-issue-types"])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert len(output) == 2
        assert output[0]["name"] == "Epic"

    def test_passes_owner_and_name_as_variables(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["--repo", "myowner/myrepo", "list-issue-types"])
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        assert "owner=myowner" in call_str
        assert "name=myrepo" in call_str

    def test_jq_filter_uses_null_safe_iteration(self) -> None:
        """Verify jq filter uses // [] fallback so null issueTypes returns []."""
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]\n", stderr=""
            )
            main(["--repo", "owner/repo", "list-issue-types"])
        call_args = mock_run.call_args[0][0]
        jq_arg_idx = call_args.index("--jq") + 1
        jq_filter = call_args[jq_arg_idx]
        assert "// []" in jq_filter

    def test_propagates_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="GraphQL error"
            )
            exit_code = main(["--repo", "owner/repo", "list-issue-types"])
        assert exit_code == 1
        assert "list-issue-types" in capsys.readouterr().err


class TestCheckResult:
    def test_returns_none_on_success(self) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok\n", stderr=""
        )
        assert check_result(result, "test-cmd") is None

    def test_returns_exit_code_on_failure(self) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="something broke"
        )
        assert check_result(result, "test-cmd") == 2

    def test_prints_stderr_with_label(self, capsys: pytest.CaptureFixture[str]) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="label 'task' not found"
        )
        check_result(result, "issue-create")
        err = capsys.readouterr().err
        assert "issue-create" in err
        assert "label 'task' not found" in err

    def test_prints_generic_message_when_no_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from github_project_tools.cli import check_result

        result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )
        check_result(result, "set-status")
        err = capsys.readouterr().err
        assert "set-status" in err
        assert "command failed" in err


class TestRunGhErrorPropagation:
    """Verify run_gh-based commands propagate errors."""

    def test_issue_view_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="issue not found"
            )
            exit_code = main(
                ["--repo", "owner/repo", "issue-view", "999", "--json", "id"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-view" in err
        assert "issue not found" in err

    def test_issue_assign_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="permission denied"
            )
            exit_code = main(["--repo", "owner/repo", "issue-assign", "42"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "issue-assign" in err

    def test_project_list_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="not found"
            )
            exit_code = main(["project-list", "--owner", "nobody"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "project-list" in err


class TestGraphqlErrorPropagation:
    """Verify graphql-based commands propagate errors."""

    def test_set_status_propagates_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="GraphQL error"
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "set-status", "PVTI_item", "done"],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "set-status" in err

    def test_add_to_project_propagates_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_config(tmp_path)
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="PVT_proj\n", stderr=""
                ),
                subprocess.CompletedProcess(
                    args=[], returncode=1, stdout="", stderr="mutation failed"
                ),
            ]
            exit_code = main(
                ["--repo", "owner/repo", "add-to-project", "I_node"],
                cwd=tmp_path,
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "add-to-project" in err

    def test_set_parent_propagates_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="not found"
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-parent", "I_child", "I_parent"]
            )
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "set-parent" in err


class TestSetIssueType:
    def test_sets_issue_type(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="Epic\n", stderr=""
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-issue-type", "I_issue123", "IT_epic"]
            )
        assert exit_code == 0
        assert capsys.readouterr().out.strip() == "Epic"

    def test_passes_correct_variables(self) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="Task\n", stderr=""
            )
            main(["--repo", "owner/repo", "set-issue-type", "I_issue123", "IT_task"])
        call_args = mock_run.call_args[0][0]
        call_str = " ".join(call_args)
        assert "id=I_issue123" in call_str
        assert "typeId=IT_task" in call_str

    def test_propagates_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("github_project_tools.cli.run_gh") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="mutation failed"
            )
            exit_code = main(
                ["--repo", "owner/repo", "set-issue-type", "I_issue123", "IT_bad"]
            )
        assert exit_code == 1
        assert "set-issue-type" in capsys.readouterr().err
