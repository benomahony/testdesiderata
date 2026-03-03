# How-to guides

Task-oriented recipes for specific goals.

---

## Configure with pyproject.toml

Add `[tool.testdesiderata]` to avoid repeating flags on every run:

```toml
[tool.testdesiderata]
select = ["DET", "FST", "ISO"]   # only run these rule prefixes
ignore = ["BHV"]                 # skip these rule prefixes
```

Config is found by walking up from the working directory. CLI flags override config values.

---

## Filter rules

Run only specific rule prefixes:

```bash
testdesiderata --select DET,FST tests/
```

Skip specific rule prefixes:

```bash
testdesiderata --ignore BHV,STR tests/
```

Prefix matching is exact: `--select DET` matches DET001–DET005, not DETAIL.

---

## Run in CI (GitHub Actions)

```yaml
- name: Lint tests
  run: |
    pip install testdesiderata
    testdesiderata tests/
```

The process exits `1` on violations, failing the job. Pass `--select` or `--ignore` to tune which rules apply in CI.

---

## Detect slow tests

Run pytest with JUnit output, then pass the report to testdesiderata:

```bash
pytest --junit-xml=report.xml tests/
testdesiderata --slow 0.5 tests/
```

The CLI auto-detects `report.xml`, `junit.xml`, `test-results.xml`, and `pytest-results.xml` in the current directory. Pass `--junit PATH` to specify a different file. The `--slow` threshold defaults to `1.0` second.

---

## Use AI review

Install the AI extra and run with `--ai`:

```bash
pip install "testdesiderata[ai]"
testdesiderata --ai tests/
```

This adds WRT001 (Writable) and INS001 (Inspiring) violations using Claude to evaluate tests that the static rules cannot reach. Requires `ANTHROPIC_API_KEY` in the environment.

---

## Add to pre-commit

```yaml
repos:
  - repo: https://github.com/benomahony/testdesiderata
    rev: v0.1.0
    hooks:
      - id: testdesiderata
        args: [--ignore, BHV]   # optional: pass any CLI flags here
```

---

## Use the Python API

```python
from pathlib import Path
from testdesiderata.linter import Linter
from testdesiderata.rules.deterministic import DeterministicRule
from testdesiderata.rules.fast import FastRule

# All rules
linter = Linter()
violations = linter.lint_path(Path("tests/"))

# Custom rule subset
linter = Linter(rules=[DeterministicRule(), FastRule()])
violations = linter.lint_file(Path("tests/test_auth.py"))

for v in violations:
    print(v)  # tests/test_auth.py:14:4: DET001 [Deterministic] ...
```
