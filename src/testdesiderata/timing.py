import ast
import xml.etree.ElementTree as ET
from pathlib import Path

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_JUNIT_CANDIDATES = [
    "report.xml",
    "junit.xml",
    "test-results.xml",
    "pytest-results.xml",
]
DEFAULT_THRESHOLD = 1.0


def find_junit_xml(cwd: Path | None = None) -> Path | None:
    assert isinstance(cwd, (Path, type(None))), "cwd must be a Path or None"
    root = cwd or Path.cwd()
    assert isinstance(root, Path), "Root path must be a Path instance"
    for name in _JUNIT_CANDIDATES:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def load_junit_timings(xml_path: Path) -> dict[str, float]:
    assert xml_path is not None, "XML path must not be None"
    assert xml_path.exists(), f"JUnit XML must exist: {xml_path}"
    timings: dict[str, float] = {}
    for testcase in ET.parse(xml_path).iter("testcase"):
        classname = testcase.get("classname", "")
        name = testcase.get("name", "")
        if classname and name:
            timings[f"{classname}::{name}"] = float(testcase.get("time", 0))
    return timings


def path_to_classname(filename: str) -> str:
    assert filename, "Filename must not be empty"
    assert isinstance(filename, str), "Filename must be a string"
    return str(Path(filename).with_suffix("")).replace("/", ".").replace("\\", ".")


class SlowTestRule:
    rule_id: str = "FST"
    desideratum: str = "Fast"

    def __init__(
        self, timing_data: dict[str, float], threshold: float = DEFAULT_THRESHOLD
    ) -> None:
        assert timing_data is not None, "Timing data must not be None"
        assert threshold > 0, "Threshold must be positive"
        self.timing_data: dict[str, float] = timing_data
        self.threshold: float = threshold

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        classname = path_to_classname(filename)
        violations: list[Violation] = []
        for func in test_functions(tree):
            duration = self.timing_data.get(
                f"{classname}::{func.name}"
            ) or self._by_name(func.name)
            if duration is not None and duration > self.threshold:
                violations.append(
                    Violation(
                        filename,
                        func.lineno,
                        func.col_offset,
                        "FST003",
                        "Fast",
                        f"test took {duration:.2f}s (threshold: {self.threshold:.1f}s) — consider splitting or using fixtures",
                    )
                )
        return violations

    def _by_name(self, func_name: str) -> float | None:
        assert func_name, "Function name must not be empty"
        assert isinstance(func_name, str), "Function name must be a string"
        suffix = f"::{func_name}"
        return next(
            (d for k, d in self.timing_data.items() if k.endswith(suffix)), None
        )
