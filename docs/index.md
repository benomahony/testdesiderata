# testdesiderata

A Python test linter that checks your test suite against [Kent Beck's 12 Test Desiderata](https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b4) via static analysis.

No test execution required — all checks run on the AST.

## Installation

```bash
pip install testdesiderata
```

With AI-powered review (Writable + Inspiring desiderata):

```bash
pip install "testdesiderata[ai]"
```

With MCP server for AI assistant integration:

```bash
pip install "testdesiderata[mcp]"
```

## Usage

### CLI

```bash
testdesiderata tests/                     # lint a directory
testdesiderata tests/test_auth.py         # lint a single file
testdesiderata --select DET,FST tests/    # only deterministic + fast rules
testdesiderata --ignore BHV tests/        # skip behavioral rules
testdesiderata --ai tests/                # include AI review (requires [ai])
```

Exit code `0` = no violations, `1` = violations found.

### Python API

```python
from pathlib import Path
from testdesiderata.linter import Linter

linter = Linter()
violations = linter.lint_path(Path("tests/"))

for v in violations:
    print(v)  # tests/test_auth.py:14:4: DET001 [Deterministic] ...
```

Custom rule subset:

```python
from testdesiderata.rules.deterministic import DeterministicRule
from testdesiderata.rules.fast import FastRule

linter = Linter(rules=[DeterministicRule(), FastRule()])
```

### pre-commit

```yaml
repos:
  - repo: https://github.com/benomahony/testdesiderata
    rev: v0.1.0
    hooks:
      - id: testdesiderata
```

## Configuration

`[tool.testdesiderata]` in `pyproject.toml`:

```toml
[tool.testdesiderata]
select = ["DET", "FST", "ISO"]
ignore = ["BHV"]
```

Config is searched from the current directory upward. CLI flags override config file values.

## Development

```bash
git clone https://github.com/benomahony/testdesiderata
cd testdesiderata
uv sync
uv run pytest tests/ -q
uv run pre-commit run --all-files
```
