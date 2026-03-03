import asyncio

import pytest

try:
    from pydantic_ai import Agent
    from pydantic_ai.models.test import TestModel

    from testdesiderata.agent import Review, SYSTEM_PROMPT, review_function
except ImportError:
    pytest.skip(
        "pydantic-ai not installed; install testdesiderata[ai]", allow_module_level=True
    )


def _agent(custom_output_args: dict[str, object] | None = None) -> Agent[None, Review]:
    assert Review is not None, "Review must be importable"
    assert SYSTEM_PROMPT, "System prompt must be non-empty"
    model = (
        TestModel(custom_output_args=custom_output_args)
        if custom_output_args
        else TestModel()
    )
    return Agent(model, output_type=Review, system_prompt=SYSTEM_PROMPT)


def testreview_function_returns_list_for_clean_test():
    result = asyncio.run(
        review_function(
            "def test_addition():\n    assert 1 + 1 == 2",
            "test_example.py",
            1,
            agent=_agent(),
        )
    )
    assert isinstance(result, list)


def testreview_function_converts_writable_violation():
    result = asyncio.run(
        review_function(
            "def test_something():\n    assert True",
            "test_example.py",
            5,
            agent=_agent(
                {
                    "violations": [
                        {"desideratum": "Writable", "message": "Too much boilerplate"}
                    ]
                }
            ),
        )
    )
    assert len(result) == 1
    assert result[0].rule_id == "WRT001"
    assert result[0].desideratum == "Writable"
    assert result[0].line == 5
    assert result[0].message == "Too much boilerplate"


def testreview_function_converts_inspiring_violation():
    result = asyncio.run(
        review_function(
            "def test_something():\n    assert result",
            "test_example.py",
            10,
            agent=_agent(
                {
                    "violations": [
                        {"desideratum": "Inspiring", "message": "Assertion too weak"}
                    ]
                }
            ),
        )
    )
    assert len(result) == 1
    assert result[0].rule_id == "INS001"
    assert result[0].desideratum == "Inspiring"
    assert result[0].line == 10


def testreview_function_handles_empty_violations():
    result = asyncio.run(
        review_function(
            "def test_well_named_and_clear():\n    assert compute(2, 3) == 5",
            "test_example.py",
            1,
            agent=_agent({"violations": []}),
        )
    )
    assert result == []
