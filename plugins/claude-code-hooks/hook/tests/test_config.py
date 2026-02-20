import json
from pathlib import Path

import pytest

from claude_code_hooks.config import load_config


class TestClaudeShimConfig:
    def test_valid_config(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {
                "include": [
                    {
                        "pattern": "**/*.ts",
                        "commands": ["npx prettier --write"],
                    }
                ],
                "exclude": ["node_modules"],
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert len(result.quality_checks.include) == 1
        assert result.quality_checks.include[0].pattern == "**/*.ts"
        assert result.quality_checks.include[0].commands == ["npx prettier --write"]
        assert result.quality_checks.exclude == ["node_modules"]

    def test_no_config_file_returns_none(self, tmp_path: Path) -> None:
        result = load_config(tmp_path)
        assert result is None

    def test_no_quality_checks_key_returns_none(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps({"other-key": {}}))

        result = load_config(tmp_path)
        assert result is None

    def test_empty_exclude_defaults(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {
                "include": [{"pattern": "**/*.py", "commands": ["ruff check"]}]
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert result.quality_checks.exclude == []

    def test_invalid_config_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(
            json.dumps({"quality-checks": {"include": "not-a-list"}})
        )

        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_multiple_include_entries(self, tmp_path: Path) -> None:
        config_data = {
            "quality-checks": {
                "include": [
                    {"pattern": "**/*.ts", "commands": ["cmd1"]},
                    {"pattern": "**/*.py", "commands": ["cmd2", "cmd3"]},
                ]
            }
        }
        config_file = tmp_path / ".claude-shim.json"
        config_file.write_text(json.dumps(config_data))

        result = load_config(tmp_path)

        assert result is not None
        assert len(result.quality_checks.include) == 2
        assert result.quality_checks.include[1].commands == ["cmd2", "cmd3"]
