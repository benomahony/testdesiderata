import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_DEBUGGER_MODULES = {"pdb", "ipdb", "pudb"}
_DEBUGGER_METHODS = {"set_trace", "post_mortem", "pm"}


def _is_interactive_builtin(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    if isinstance(node.func, ast.Name) and node.func.id in {"input", "breakpoint"}:
        return node.func.id
    return None


def _is_debugger_call(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    if (
        isinstance(func, ast.Attribute)
        and func.attr in _DEBUGGER_METHODS
        and isinstance(func.value, ast.Name)
        and func.value.id in _DEBUGGER_MODULES
    ):
        return f"{func.value.id}.{func.attr}"
    return None


class AutomatedRule:
    rule_id: str = "AUT"
    desideratum: str = "Automated"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for node in ast.walk(func):
                if not isinstance(node, ast.Call):
                    continue
                name = _is_interactive_builtin(node)
                if name:
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "AUT001",
                            "Automated",
                            f"{name}() requires human intervention — tests must run without interaction",
                        )
                    )
                    continue
                dbg = _is_debugger_call(node)
                if dbg:
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "AUT002",
                            "Automated",
                            f"{dbg}() is a debugger call — tests must run without human intervention",
                        )
                    )
        return violations
