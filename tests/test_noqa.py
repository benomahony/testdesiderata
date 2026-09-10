import ast
import textwrap
from pathlib import Path

import pytest

from testdesiderata.linter import Linter
from testdesiderata.noqa import filter_noqa
from testdesiderata.rules.deterministic import DeterministicRule

pytestmark = pytest.mark.unit


def _det_violations(source: str) -> list[str]:
    tree = ast.parse(textwrap.dedent(source))
    return [v.rule_id for v in DeterministicRule().check(tree, "test_example.py")]


def _filtered(source: str) -> list[str]:
    source = textwrap.dedent(source)
    tree = ast.parse(source)
    violations = DeterministicRule().check(tree, "test_example.py")
    return [v.rule_id for v in filter_noqa(violations, source)]


def test_noqa_specific_code_suppresses_matching_violation():
    assert _det_violations("""
        def test_something():
            import random
            x = random.randint(1, 10)
            assert x > 0
    """) == ["DET001"]
    assert (
        _filtered("""
        def test_something():
            import random
            x = random.randint(1, 10)  # noqa: DET001
            assert x > 0
    """)
        == []
    )


def test_noqa_specific_code_does_not_suppress_other_codes():
    assert _filtered("""
        def test_something():
            import random
            x = random.randint(1, 10)  # noqa: ISO001
            assert x > 0
    """) == ["DET001"]


def test_noqa_bare_suppresses_everything_on_the_line():
    assert (
        _filtered("""
        def test_something():
            import random
            x = random.randint(1, 10)  # noqa
            assert x > 0
    """)
        == []
    )


def test_noqa_prefix_suppresses_whole_category():
    assert (
        _filtered("""
        def test_something():
            import random
            x = random.randint(1, 10)  # noqa: DET
            assert x > 0
    """)
        == []
    )


def test_noqa_in_string_literal_is_not_treated_as_a_comment():
    assert _filtered("""
        def test_something():
            import random
            x = random.randint(1, 10)
            assert x > 0, "not noqa: DET001, just text"
    """) == ["DET001"]


def test_lint_file_respects_noqa(tmp_path: Path):
    source = textwrap.dedent("""
        def test_something():
            import random
            x = random.randint(1, 10)  # noqa: DET001
            assert x > 0
    """)
    _ = (tmp_path / "test_suppressed.py").write_text(source)
    violations = Linter().lint_file(tmp_path / "test_suppressed.py")
    assert violations == []
