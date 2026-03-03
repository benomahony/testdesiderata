import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

MAX_ASSERTIONS = 10
MAX_TEST_LINES = 50


class ComposableRule:
    rule_id: str = "CMP"
    desideratum: str = "Composable"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            assert_count = sum(1 for n in ast.walk(func) if isinstance(n, ast.Assert))
            if assert_count > MAX_ASSERTIONS:
                violations.append(
                    Violation(
                        filename,
                        func.lineno,
                        func.col_offset,
                        "CMP001",
                        "Composable",
                        f"{assert_count} assertions in one test (max {MAX_ASSERTIONS}): split into focused tests",
                    )
                )
            end = func.end_lineno if func.end_lineno is not None else func.lineno
            length = end - func.lineno
            if length > MAX_TEST_LINES:
                violations.append(
                    Violation(
                        filename,
                        func.lineno,
                        func.col_offset,
                        "CMP002",
                        "Composable",
                        f"test is {length} lines (max {MAX_TEST_LINES}): split into smaller composable tests",
                    )
                )
        return violations
