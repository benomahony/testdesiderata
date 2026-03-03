import ast
import textwrap
from pathlib import Path

from testdesiderata.timing import (
    SlowTestRule,
    find_junit_xml,
    load_junit_timings,
    path_to_classname,
)

_JUNIT_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="3">
    <testcase classname="tests.test_foo" name="test_fast" time="0.02"/>
    <testcase classname="tests.test_foo" name="test_slow" time="2.50"/>
    <testcase classname="tests.test_bar" name="test_medium" time="0.80"/>
  </testsuite>
</testsuites>
"""


def test_load_junit_timings(tmp_path: Path):
    xml = tmp_path / "report.xml"
    _ = xml.write_text(_JUNIT_XML)
    timings = load_junit_timings(xml)
    assert timings["tests.test_foo::test_fast"] == 0.02
    assert timings["tests.test_foo::test_slow"] == 2.50
    assert timings["tests.test_bar::test_medium"] == 0.80


def test_find_junit_xml_detects_report(tmp_path: Path):
    _ = (tmp_path / "report.xml").write_text(_JUNIT_XML)
    found = find_junit_xml(tmp_path)
    assert found == tmp_path / "report.xml"


def test_find_junit_xml_returns_none_when_absent(tmp_path: Path):
    result = find_junit_xml(tmp_path)
    assert result is None


def test_path_to_classname():
    assert path_to_classname("tests/test_foo.py") == "tests.test_foo"
    assert path_to_classname("test_bar.py") == "test_bar"


def test_slow_test_rule_flags_exceeding_threshold():
    timings = {"tests.test_foo::test_slow": 2.5}
    rule = SlowTestRule(timings, threshold=1.0)
    tree = ast.parse(
        textwrap.dedent("""
        def test_slow():
            assert True
    """)
    )
    violations = rule.check(tree, "tests/test_foo.py")
    assert len(violations) == 1
    assert violations[0].rule_id == "FST003"
    assert "2.50s" in violations[0].message


def test_slow_test_rule_passes_fast_tests():
    timings = {"tests.test_foo::test_fast": 0.02}
    rule = SlowTestRule(timings, threshold=1.0)
    tree = ast.parse(
        textwrap.dedent("""
        def test_fast():
            assert True
    """)
    )
    violations = rule.check(tree, "tests/test_foo.py")
    assert violations == []


def test_slow_test_rule_falls_back_to_name_match():
    timings = {"some.other.module::test_slow": 3.0}
    rule = SlowTestRule(timings, threshold=1.0)
    tree = ast.parse(
        textwrap.dedent("""
        def test_slow():
            assert True
    """)
    )
    violations = rule.check(tree, "tests/test_foo.py")
    assert len(violations) == 1
    assert "3.00s" in violations[0].message
