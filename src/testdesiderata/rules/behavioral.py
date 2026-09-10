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


def _is_patch_call(node: ast.Call) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    return _is_patch_decorator(node)


def _has_autospec_false(node: ast.Call) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    return any(
        kw.arg == "autospec"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is False
        for kw in node.keywords
    )


def _is_spy_call(node: ast.Call) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "spy"
        and isinstance(func.value, ast.Name)
        and func.value.id == "mocker"
    )


def _mock_name(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


class BehavioralRule:
    rule_id: str = "BHV"
    desideratum: str = "Behavioral"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            violations.extend(self._check_decorators(func, filename))
            for node in ast.walk(func):
                if isinstance(node, ast.Call):
                    violations.extend(self._check_call(node, filename))
        return violations

    def _check_decorators(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef, filename: str
    ) -> list[Violation]:
        assert func is not None, "Function node must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
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
        return violations

    def _check_call(self, node: ast.Call, filename: str) -> list[Violation]:
        assert node is not None, "Call node must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        if _is_mock_creation(node) and (name := _mock_name(node)):
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
        if _is_spy_call(node):
            violations.append(
                Violation(
                    filename,
                    node.lineno,
                    node.col_offset,
                    "BHV003",
                    "Behavioral",
                    "mocker.spy() still asserts on call metadata rather than observable behavior",
                )
            )
        if _is_patch_call(node) and _has_autospec_false(node):
            violations.append(
                Violation(
                    filename,
                    node.lineno,
                    node.col_offset,
                    "BHV004",
                    "Behavioral",
                    "patch(..., autospec=False) lets the mock accept calls the real object would reject",
                )
            )
        return violations
