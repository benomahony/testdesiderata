import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_MOCK_ASSERT_RULES: dict[str, str] = {
    "assert_called_with": "STR001",
    "assert_called_once_with": "STR002",
    "assert_called_once": "STR003",
    "assert_not_called": "STR004",
    "assert_any_call": "STR005",
    "assert_has_calls": "STR006",
}

_CALL_ATTR_RULES: dict[str, str] = {
    "call_count": "STR007",
    "call_args": "STR008",
    "call_args_list": "STR008",
}


class StructureInsensitiveRule:
    rule_id: str = "STR"
    desideratum: str = "Structure-insensitive"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for node in ast.walk(func):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    rule_id = _MOCK_ASSERT_RULES.get(node.func.attr)
                    if rule_id:
                        violations.append(
                            Violation(
                                filename,
                                node.lineno,
                                node.col_offset,
                                rule_id,
                                "Structure-insensitive",
                                f".{node.func.attr}() asserts call structure, not observable behavior",
                            )
                        )
                elif isinstance(node, ast.Attribute):
                    rule_id = _CALL_ATTR_RULES.get(node.attr)
                    if rule_id:
                        violations.append(
                            Violation(
                                filename,
                                node.lineno,
                                node.col_offset,
                                rule_id,
                                "Structure-insensitive",
                                f".{node.attr} inspects call structure, not observable behavior",
                            )
                        )
        return violations
