import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_MOCK_CLASSES = {
    "Mock",
    "MagicMock",
    "AsyncMock",
    "NonCallableMock",
    "NonCallableMagicMock",
}


def _is_mock_creation(node: ast.Call) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    if isinstance(func, ast.Name) and func.id in _MOCK_CLASSES:
        return True
    return (
        isinstance(func, ast.Attribute)
        and func.attr in _MOCK_CLASSES
        and isinstance(func.value, ast.Name)
        and func.value.id in {"mock", "unittest"}
    )


def _is_patch_decorator(deco: ast.expr) -> bool:
    assert deco is not None, "Decorator node must not be None"
    assert isinstance(deco, ast.AST), "Decorator must be an AST node"
    node = deco.func if isinstance(deco, ast.Call) else deco
    if isinstance(node, ast.Name) and node.id == "patch":
        return True
    return (
        isinstance(node, ast.Attribute)
        and node.attr in {"patch", "object"}
        and isinstance(node.value, ast.Name)
        and node.value.id in {"mock", "unittest"}
    )


class BehavioralRule:
    rule_id: str = "BHV"
    desideratum: str = "Behavioral"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for deco in func.decorator_list:
                if _is_patch_decorator(deco):
                    violations.append(
                        Violation(
                            filename,
                            deco.lineno,
                            deco.col_offset,
                            "BHV002",
                            "Behavioral",
                            "@patch couples the test to internal implementation details",
                        )
                    )
            for node in ast.walk(func):
                if isinstance(node, ast.Call) and _is_mock_creation(node):
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        name = node.func.attr
                    else:
                        continue
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "BHV001",
                            "Behavioral",
                            f"{name}() substitutes real behavior — tests may miss behavioral regressions",
                        )
                    )
        return violations
