import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions


def _is_sleep_call(node: ast.Call) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    is_attr = (
        isinstance(func, ast.Attribute)
        and func.attr == "sleep"
        and isinstance(func.value, ast.Name)
        and func.value.id == "time"
    )
    is_name = isinstance(func, ast.Name) and func.id == "sleep"
    return is_attr or is_name


def _has_nested_for(stmts: list[ast.stmt]) -> bool:
    assert stmts is not None, "Statement list must not be None"
    assert isinstance(stmts, list), "Statements must be a list"
    return any(isinstance(s, (ast.For, ast.AsyncFor)) for s in stmts)


class FastRule:
    rule_id: str = "FST"
    desideratum: str = "Fast"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for node in ast.walk(func):
                if isinstance(node, ast.Call) and _is_sleep_call(node):
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "FST001",
                            "Fast",
                            "time.sleep() in tests slows down the suite",
                        )
                    )
                elif isinstance(node, (ast.For, ast.AsyncFor)) and _has_nested_for(
                    node.body
                ):
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "FST002",
                            "Fast",
                            "nested loops in tests suggest O(n²) work; extract to fixtures or parametrize",
                        )
                    )
        return violations
