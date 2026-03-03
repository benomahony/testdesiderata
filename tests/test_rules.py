import ast
import textwrap

import pytest

from testdesiderata.linter import Linter
from testdesiderata.rules.automated import AutomatedRule
from testdesiderata.rules.behavioral import BehavioralRule
from testdesiderata.rules.composable import ComposableRule
from testdesiderata.rules.deterministic import DeterministicRule
from testdesiderata.rules.fast import FastRule
from testdesiderata.rules.isolated import IsolatedRule
from testdesiderata.rules.predictive import PredictiveRule
from testdesiderata.rules.readable import ReadableRule
from testdesiderata.rules.specific import SpecificRule
from testdesiderata.rules.structure_insensitive import StructureInsensitiveRule


def parse(source: str) -> ast.AST:
    return ast.parse(textwrap.dedent(source))


def violations_for(rule, source: str) -> list[str]:
    return [v.rule_id for v in rule.check(parse(source), "test_example.py")]


def test_det001_random_call():
    ids = violations_for(
        DeterministicRule(),
        """
        def test_something():
            import random
            x = random.randint(1, 10)
            assert x > 0
    """,
    )
    assert ids == ["DET001"]


def test_det002_datetime_now():
    ids = violations_for(
        DeterministicRule(),
        """
        import datetime
        def test_something():
            now = datetime.datetime.now()
            assert now is not None
    """,
    )
    assert ids == ["DET002"]


def test_det003_time_time():
    ids = violations_for(
        DeterministicRule(),
        """
        import time
        def test_something():
            t = time.time()
            assert t > 0
    """,
    )
    assert ids == ["DET003"]


def test_det004_uuid4():
    ids = violations_for(
        DeterministicRule(),
        """
        import uuid
        def test_something():
            uid = uuid.uuid4()
            assert uid is not None
    """,
    )
    assert ids == ["DET004"]


def test_iso001_global_statement():
    ids = violations_for(
        IsolatedRule(),
        """
        counter = 0
        def test_increments():
            global counter
            counter += 1
            assert counter == 1
    """,
    )
    assert ids == ["ISO001"]


def test_iso002_environ_mutation():
    ids = violations_for(
        IsolatedRule(),
        """
        import os
        def test_something():
            os.environ["KEY"] = "value"
            assert os.environ["KEY"] == "value"
    """,
    )
    assert ids == ["ISO002"]


def test_iso003_open_builtin():
    ids = violations_for(
        IsolatedRule(),
        """
        def test_something():
            with open("data.txt") as f:
                data = f.read()
            assert data
    """,
    )
    assert "ISO003" in ids


def test_iso003_write_text():
    ids = violations_for(
        IsolatedRule(),
        """
        from pathlib import Path
        def test_something():
            Path("out.txt").write_text("hello")
            assert True
    """,
    )
    assert "ISO003" in ids


def test_iso004_requests_get():
    ids = violations_for(
        IsolatedRule(),
        """
        import requests
        def test_something():
            r = requests.get("https://api.example.com/data")
            assert r.status_code == 200
    """,
    )
    assert "ISO004" in ids


def test_iso005_sqlite3_connect():
    ids = violations_for(
        IsolatedRule(),
        """
        import sqlite3
        def test_something():
            conn = sqlite3.connect(":memory:")
            assert conn is not None
    """,
    )
    assert "ISO005" in ids


def test_iso005_create_engine():
    ids = violations_for(
        IsolatedRule(),
        """
        from sqlalchemy import create_engine
        def test_something():
            engine = create_engine("sqlite:///:memory:")
            assert engine is not None
    """,
    )
    assert "ISO005" in ids


def test_fst001_sleep():
    ids = violations_for(
        FastRule(),
        """
        import time
        def test_something():
            time.sleep(0.1)
            assert True
    """,
    )
    assert ids == ["FST001"]


def test_fst002_polling_loop():
    ids = violations_for(
        FastRule(),
        """
        import time
        def test_something():
            for _ in range(10):
                time.sleep(0.1)
            assert True
    """,
    )
    assert "FST002" in ids


def test_fst002_nested_loop_without_sleep_is_clean():
    ids = violations_for(
        FastRule(),
        """
        def test_something():
            for i in range(3):
                for j in range(3):
                    assert i != j or True
    """,
    )
    assert "FST002" not in ids


def test_aut001_input_call():
    ids = violations_for(
        AutomatedRule(),
        """
        def test_something():
            name = input("enter name: ")
            assert name != ""
    """,
    )
    assert ids == ["AUT001"]


def test_aut002_breakpoint():
    ids = violations_for(
        AutomatedRule(),
        """
        def test_something():
            breakpoint()
            assert True
    """,
    )
    assert ids == ["AUT001"]


def test_aut002_pdb_set_trace():
    ids = violations_for(
        AutomatedRule(),
        """
        import pdb
        def test_something():
            pdb.set_trace()
            assert True
    """,
    )
    assert ids == ["AUT002"]


def test_bhv001_mock_creation():
    ids = violations_for(
        BehavioralRule(),
        """
        from unittest.mock import MagicMock
        def test_something():
            m = MagicMock()
            m.method.return_value = 42
            assert m.method() == 42
    """,
    )
    assert ids == ["BHV001"]


def test_bhv002_patch_decorator():
    ids = violations_for(
        BehavioralRule(),
        """
        from unittest.mock import patch
        @patch("mymodule.MyClass")
        def test_something(mock_cls):
            mock_cls.return_value = 42
            assert mock_cls() == 42
    """,
    )
    assert ids == ["BHV002"]


def test_str001_assert_called_with():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            mock.assert_called_with(1, 2)
    """,
    )
    assert ids == ["STR001"]


def test_str002_assert_called_once_with():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            mock.assert_called_once_with(1, 2)
    """,
    )
    assert ids == ["STR002"]


def test_str003_assert_called_once():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            mock.assert_called_once()
    """,
    )
    assert ids == ["STR003"]


def test_str004_assert_not_called():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            mock.assert_not_called()
    """,
    )
    assert ids == ["STR004"]


def test_str005_assert_any_call():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            mock.assert_any_call(1)
    """,
    )
    assert ids == ["STR005"]


def test_str006_assert_has_calls():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            mock.assert_has_calls([])
    """,
    )
    assert ids == ["STR006"]


def test_str007_call_count():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            assert mock.call_count == 1
    """,
    )
    assert ids == ["STR007"]


def test_str008_call_args():
    ids = violations_for(
        StructureInsensitiveRule(),
        """
        def test_something():
            mock = object()
            assert mock.call_args == ((1,), {})
    """,
    )
    assert ids == ["STR008"]


def test_spc001_bare_except():
    ids = violations_for(
        SpecificRule(),
        """
        def test_something():
            try:
                pass
            except:
                pass
    """,
    )
    assert ids == ["SPC001"]


def test_spc001_broad_exception():
    ids = violations_for(
        SpecificRule(),
        """
        def test_something():
            try:
                pass
            except Exception:
                pass
    """,
    )
    assert ids == ["SPC001"]


def test_spc002_compound_assert_no_message():
    ids = violations_for(
        SpecificRule(),
        """
        def test_something():
            x, y = 1, 2
            assert x > 0 and y > 0
    """,
    )
    assert ids == ["SPC002"]


def test_spc002_clean_with_message():
    ids = violations_for(
        SpecificRule(),
        """
        def test_something():
            x, y = 1, 2
            assert x > 0 and y > 0, "both must be positive"
    """,
    )
    assert ids == []


def test_prd001_skip_in_body():
    ids = violations_for(
        PredictiveRule(),
        """
        import pytest
        def test_something():
            pytest.skip("not ready")
            assert True
    """,
    )
    assert "PRD001" in ids


def test_prd002_skip_decorator():
    ids = violations_for(
        PredictiveRule(),
        """
        import pytest
        @pytest.mark.skip
        def test_something():
            assert True
    """,
    )
    assert ids == ["PRD002"]


def test_prd003_xfail_no_strict():
    ids = violations_for(
        PredictiveRule(),
        """
        import pytest
        @pytest.mark.xfail
        def test_something():
            assert False
    """,
    )
    assert ids == ["PRD003"]


def test_prd003_xfail_strict_is_clean():
    ids = violations_for(
        PredictiveRule(),
        """
        import pytest
        @pytest.mark.xfail(strict=True)
        def test_something():
            assert False
    """,
    )
    assert ids == []


def test_cmp001_too_many_assertions():
    assert_lines = "\n    ".join(f"assert x > {i}" for i in range(12))
    source = f"def test_something():\n    x = 100\n    {assert_lines}"
    ids = violations_for(ComposableRule(), source)
    assert ids == ["CMP001"]


def test_rdl001_non_descriptive_name():
    ids = violations_for(
        ReadableRule(),
        """
        def test_foo():
            assert True
    """,
    )
    assert ids == ["RDL001"]


def test_rdl001_descriptive_name_is_clean():
    ids = violations_for(
        ReadableRule(),
        """
        def test_user_can_log_in_with_valid_credentials():
            assert True
    """,
    )
    assert ids == []


def test_clean_test_has_no_violations():
    linter = Linter()
    violations = linter.lint_tree(
        parse("""
        def test_addition_returns_correct_sum():
            result = 1 + 2
            assert result == 3
    """),
        "test_clean.py",
    )
    assert violations == []


@pytest.mark.parametrize(
    "source,expected_rule",
    [
        ("def test_foo():\n    import random\n    random.random()", "DET001"),
        ("def test_foo():\n    global x\n    x = 1", "ISO001"),
        ("def test_foo():\n    import time\n    time.sleep(1)", "FST001"),
        ("def test_foo():\n    breakpoint()", "AUT001"),
    ],
)
def test_parametrized_rule_detection(source: str, expected_rule: str):
    linter = Linter()
    violations = linter.lint_tree(ast.parse(source), "test_example.py")
    rule_ids = [v.rule_id for v in violations]
    assert expected_rule in rule_ids
