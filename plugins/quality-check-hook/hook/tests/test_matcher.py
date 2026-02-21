from quality_check_hook.config import QualityCheckEntry, QualityChecks
from quality_check_hook.matcher import collect_commands


class TestCollectCommands:
    def test_single_pattern_match(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
        )
        result = collect_commands("src/app.ts", checks)
        assert result == ["cmd1"]

    def test_single_pattern_no_match(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
        )
        result = collect_commands("src/app.py", checks)
        assert result == []

    def test_brace_expansion(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.{ts,tsx}", commands=["prettier"])],
        )
        assert collect_commands("src/app.ts", checks) == ["prettier"]
        assert collect_commands("src/app.tsx", checks) == ["prettier"]
        assert collect_commands("src/app.js", checks) == []

    def test_multiple_patterns_same_file(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(
                    pattern="**/*.{js,ts}", commands=["prettier", "eslint --fix"]
                ),
                QualityCheckEntry(pattern="**/*.ts", commands=["eslint"]),
            ],
        )
        result = collect_commands("src/app.ts", checks)
        assert result == ["prettier", "eslint --fix", "eslint"]

    def test_multiple_patterns_partial_match(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(pattern="**/*.{js,ts}", commands=["prettier"]),
                QualityCheckEntry(pattern="**/*.ts", commands=["tsc"]),
            ],
        )
        result = collect_commands("src/app.js", checks)
        assert result == ["prettier"]

    def test_exclude_filters_file(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
            exclude=["node_modules"],
        )
        result = collect_commands("node_modules/pkg/index.ts", checks)
        assert result == []

    def test_exclude_glob_pattern(self) -> None:
        checks = QualityChecks(
            include=[QualityCheckEntry(pattern="**/*.ts", commands=["cmd1"])],
            exclude=["src/generated/**/*.ts"],
        )
        assert collect_commands("src/generated/types.ts", checks) == []
        assert collect_commands("src/app.ts", checks) == ["cmd1"]

    def test_empty_include(self) -> None:
        checks = QualityChecks(include=[])
        result = collect_commands("src/app.ts", checks)
        assert result == []

    def test_preserves_command_order(self) -> None:
        checks = QualityChecks(
            include=[
                QualityCheckEntry(pattern="**/*", commands=["first", "second"]),
                QualityCheckEntry(pattern="**/*.ts", commands=["third"]),
            ],
        )
        result = collect_commands("src/app.ts", checks)
        assert result == ["first", "second", "third"]
