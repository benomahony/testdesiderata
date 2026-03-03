import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_BROAD_EXCEPTIONS = {"Exception", "BaseException"}


class SpecificRule:
    rule_id: str = "SPC"
    desideratum: str = "Specific"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for node in ast.walk(func):
                if isinstance(node, ast.ExceptHandler):
                    v = self._check_except(node, filename)
                    if v:
                        violations.append(v)
                elif isinstance(node, ast.Assert):
                    v = self._check_assert(node, filename)
                    if v:
                        violations.append(v)
        return violations

    def _check_except(self, node: ast.ExceptHandler, filename: str) -> Violation | None:
        assert node is not None, "ExceptHandler node must not be None"
        assert filename, "Filename must not be empty"
        if node.type is None:
            return Violation(
                filename,
                node.lineno,
                node.col_offset,
                "SPC001",
                "Specific",
                "bare except: catches everything including SystemExit; makes failures hard to diagnose",
            )
        if isinstance(node.type, ast.Name) and node.type.id in _BROAD_EXCEPTIONS:
            return Violation(
                filename,
                node.lineno,
                node.col_offset,
                "SPC001",
                "Specific",
                f"except {node.type.id}: is too broad — use a specific exception type",
            )
        return None

    def _check_assert(self, node: ast.Assert, filename: str) -> Violation | None:
        assert node is not None, "Assert node must not be None"
        assert filename, "Filename must not be empty"
        if isinstance(node.test, ast.BoolOp) and node.msg is None:
            return Violation(
                filename,
                node.lineno,
                node.col_offset,
                "SPC002",
                "Specific",
                "compound assert without message: when it fails you won't know which condition failed",
            )
        return None
