import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions


def _is_pytest_mark(node: ast.expr, mark: str) -> bool:
    assert node is not None, "Decorator node must not be None"
    assert mark, "Mark name must not be empty"
    target = node.func if isinstance(node, ast.Call) else node
    return (
        isinstance(target, ast.Attribute)
        and target.attr == mark
        and isinstance(target.value, ast.Attribute)
        and target.value.attr == "mark"
        and isinstance(target.value.value, ast.Name)
        and target.value.value.id == "pytest"
    )


def _is_pytest_direct(node: ast.expr, name: str) -> bool:
    assert node is not None, "Node must not be None"
    assert name, "Name must not be empty"
    target = node.func if isinstance(node, ast.Call) else node
    return (
        isinstance(target, ast.Attribute)
        and target.attr == name
        and isinstance(target.value, ast.Name)
        and target.value.id == "pytest"
    )


def _xfail_has_strict(node: ast.Call) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    return any(
        kw.arg == "strict"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in node.keywords
    )


class PredictiveRule:
    rule_id: str = "PRD"
    desideratum: str = "Predictive"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for deco in func.decorator_list:
                if _is_pytest_mark(deco, "skip"):
                    violations.append(
                        Violation(
                            filename,
                            deco.lineno,
                            deco.col_offset,
                            "PRD002",
                            "Predictive",
                            "@pytest.mark.skip unconditionally removes the test from the suite",
                        )
                    )
                elif _is_pytest_mark(deco, "xfail"):
                    if not isinstance(deco, ast.Call) or not _xfail_has_strict(deco):
                        violations.append(
                            Violation(
                                filename,
                                deco.lineno,
                                deco.col_offset,
                                "PRD003",
                                "Predictive",
                                "@pytest.mark.xfail without strict=True silently passes when the test unexpectedly succeeds",
                            )
                        )
            for node in ast.walk(func):
                if isinstance(node, ast.Call) and _is_pytest_direct(node, "skip"):
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "PRD001",
                            "Predictive",
                            "pytest.skip() in test body unconditionally masks a coverage gap",
                        )
                    )
        return violations
