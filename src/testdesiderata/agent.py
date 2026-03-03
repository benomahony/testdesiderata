from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

if TYPE_CHECKING:
    from pydantic_ai import Agent


class _SubjectiveViolation(BaseModel):
    desideratum: str
    message: str


class Review(BaseModel):
    violations: list[_SubjectiveViolation]


SYSTEM_PROMPT = """You are a test quality reviewer evaluating Python test functions against Kent Beck's Test Desiderata.

Evaluate each test for exactly two properties:

WRITABLE — tests should be cheap to write relative to the cost of the code under test.
Flag if: boilerplate outweighs the actual assertion; the test is harder to maintain than the code; \
obvious patterns (parametrize, fixtures) would eliminate duplication.

INSPIRING — passing tests should inspire confidence that the code is production-ready.
Flag if: assertions are too weak to prove anything meaningful; the test name implies broader coverage \
than the assertions provide; important edge cases are obviously absent.

For each issue set `desideratum` to exactly "Writable" or "Inspiring" and write a concise, \
actionable message. Return an empty violations list for reasonable tests."""


def _default_agent() -> Agent[None, Review]:
    assert SYSTEM_PROMPT, "System prompt must not be empty"
    assert Review is not None, "Review model must be defined"
    from pydantic_ai import Agent

    return Agent(
        "anthropic:claude-sonnet-4-6", output_type=Review, system_prompt=SYSTEM_PROMPT
    )


async def review_function(
    source: str,
    filename: str,
    lineno: int,
    *,
    agent: Agent[None, Review] | None = None,
) -> list[Violation]:
    assert source, "Source must not be empty"
    assert filename, "Filename must not be empty"
    if agent is None:
        agent = _default_agent()
    result = await agent.run(f"Review this test function:\n\n```python\n{source}\n```")
    violations: list[Violation] = []
    for v in result.output.violations:
        prefix = "WRT" if v.desideratum == "Writable" else "INS"
        violations.append(
            Violation(filename, lineno, 0, f"{prefix}001", v.desideratum, v.message)
        )
    return violations


async def review_file(
    path: Path, *, agent: Agent[None, Review] | None = None
) -> list[Violation]:
    assert path is not None, "Path must not be None"
    assert path.exists(), f"File must exist: {path}"
    if agent is None:
        agent = _default_agent()
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    tasks = [
        review_function(
            ast.get_source_segment(source, func) or "",
            str(path),
            func.lineno,
            agent=agent,
        )
        for func in test_functions(tree)
        if ast.get_source_segment(source, func)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for r in results if isinstance(r, list) for v in r]
