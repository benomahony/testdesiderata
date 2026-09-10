import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_RANDOM_ATTRS = {
    "random",
    "randint",
    "choice",
    "choices",
    "shuffle",
    "sample",
    "uniform",
    "gauss",
}
_TIME_ATTRS = {"time", "monotonic", "perf_counter", "process_time", "time_ns"}
_UUID_ATTRS = {"uuid1", "uuid4"}
_DATETIME_ATTRS = {"now", "today", "utcnow"}
_NUMPY_RANDOM_ATTRS = {
    "rand",
    "randn",
    "randint",
    "random",
    "choice",
    "shuffle",
    "sample",
    "uniform",
    "normal",
    "permutation",
}


def _attr_call(node: ast.Call, module: str, attrs: set[str]) -> bool:
    assert node is not None, "Call node must not be None"
    assert module, "Module name must not be empty"
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in attrs
        and isinstance(func.value, ast.Name)
        and func.value.id == module
    )


def _nested_attr_call(node: ast.Call, outer: str, inner: str, attrs: set[str]) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in attrs
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == inner
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id == outer
    )


def _numpy_random_prefix(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    for outer in ("numpy", "np"):
        if _nested_attr_call(node, outer, "random", _NUMPY_RANDOM_ATTRS):
            return outer
    return None


class DeterministicRule:
    rule_id: str = "DET"
    desideratum: str = "Deterministic"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for node in ast.walk(func):
                if isinstance(node, ast.Call):
                    v = self._check_call(node, filename)
                    if v:
                        violations.append(v)
        return violations

    def _check_call(self, node: ast.Call, filename: str) -> Violation | None:
        assert node is not None, "Call node must not be None"
        assert filename, "Filename must not be empty"
        attr = node.func.attr if isinstance(node.func, ast.Attribute) else None
        numpy_prefix = _numpy_random_prefix(node)
        matches: list[tuple[bool, str, str]] = [
            (
                _attr_call(node, "random", _RANDOM_ATTRS),
                "DET001",
                f"random.{attr}() produces non-deterministic results",
            ),
            (
                _attr_call(node, "time", _TIME_ATTRS)
                or _nested_attr_call(node, "time", "time", _TIME_ATTRS),
                "DET003",
                f"time.{attr}() returns a non-deterministic value",
            ),
            (
                _attr_call(node, "datetime", _DATETIME_ATTRS)
                or _nested_attr_call(node, "datetime", "datetime", _DATETIME_ATTRS),
                "DET002",
                f"datetime.{attr}() returns the non-deterministic current time",
            ),
            (
                _attr_call(node, "uuid", _UUID_ATTRS),
                "DET004",
                f"uuid.{attr}() generates a non-deterministic value",
            ),
            (
                _attr_call(node, "os", {"urandom"}),
                "DET005",
                "os.urandom() generates non-deterministic bytes",
            ),
            (
                numpy_prefix is not None,
                "DET006",
                f"{numpy_prefix}.random.{attr}() produces non-deterministic results unless seeded",
            ),
        ]
        for matched, rule_id, message in matches:
            if matched:
                return Violation(
                    filename,
                    node.lineno,
                    node.col_offset,
                    rule_id,
                    "Deterministic",
                    message,
                )
        return None
