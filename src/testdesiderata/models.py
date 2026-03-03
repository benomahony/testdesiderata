import ast
from dataclasses import dataclass
from typing import Protocol, override


class Rule(Protocol):
    rule_id: str

    def check(self, tree: ast.AST, filename: str) -> "list[Violation]":
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        return []


@dataclass(frozen=True)
class Violation:
    filename: str
    line: int
    col: int
    rule_id: str
    desideratum: str
    message: str

    @override
    def __str__(self) -> str:
        assert self.filename, "Filename must not be empty"
        assert self.rule_id, "Rule ID must not be empty"
        return f"{self.filename}:{self.line}:{self.col}: {self.rule_id} [{self.desideratum}] {self.message}"
