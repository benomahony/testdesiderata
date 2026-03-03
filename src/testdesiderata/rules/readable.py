import ast
import re

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_SHORT_NAME_PATTERN = r"^test_?\w{0,5}$"
MIN_COMPLEX_LINES = 20


def _has_docstring(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    assert func is not None, "Function node must not be None"
    assert isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)), (
        "Func must be a function definition"
    )
    return (
        bool(func.body)
        and isinstance(func.body[0], ast.Expr)
        and isinstance(func.body[0].value, ast.Constant)
        and isinstance(func.body[0].value.value, str)
    )


class ReadableRule:
    rule_id: str = "RDL"
    desideratum: str = "Readable"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            if re.match(_SHORT_NAME_PATTERN, func.name):
                violations.append(
                    Violation(
                        filename,
                        func.lineno,
                        func.col_offset,
                        "RDL001",
                        "Readable",
                        f"'{func.name}' is non-descriptive: use a name that describes the expected behavior",
                    )
                )
            end = func.end_lineno if func.end_lineno is not None else func.lineno
            if (end - func.lineno) > MIN_COMPLEX_LINES and not _has_docstring(func):
                violations.append(
                    Violation(
                        filename,
                        func.lineno,
                        func.col_offset,
                        "RDL002",
                        "Readable",
                        f"'{func.name}' is complex ({end - func.lineno} lines) but has no docstring explaining its purpose",
                    )
                )
        return violations
