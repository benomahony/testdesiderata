import ast
from pathlib import Path

from testdesiderata.models import Rule, Violation
from testdesiderata.rules import ALL_RULES


class Linter:
    rules: list[Rule]

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules if rules is not None else ALL_RULES
        assert self.rules is not None, "Rules list must not be None"
        assert len(self.rules) > 0, "Must have at least one rule"

    def lint_tree(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for rule in self.rules:
            violations.extend(rule.check(tree, filename))
        return sorted(violations, key=lambda v: (v.filename, v.line, v.col, v.rule_id))

    def lint_file(self, path: Path) -> list[Violation]:
        assert path is not None, "Path must not be None"
        assert path.exists(), f"File does not exist: {path}"
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError:
            return []
        return self.lint_tree(tree, str(path))

    def lint_path(self, path: Path) -> list[Violation]:
        assert path is not None, "Path must not be None"
        assert isinstance(path, Path), "Path must be a Path instance"
        if path.is_file():
            return self.lint_file(path)
        violations: list[Violation] = []
        for pattern in ("test_*.py", "*_test.py"):
            for py_file in sorted(path.rglob(pattern)):
                violations.extend(self.lint_file(py_file))
        return sorted(violations, key=lambda v: (v.filename, v.line, v.col, v.rule_id))
