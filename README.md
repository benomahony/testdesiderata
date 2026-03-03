# testdesiderata

Lint Python test files against [Kent Beck's 12 Test Desiderata](https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b4). Static analysis only — no test execution required.

```
$ testdesiderata tests/

tests/test_payment.py
  14:4  DET001  [Deterministic]  random.choice() produces non-deterministic results
  31:8  ISO003  [Isolated]       open() in tests creates file system dependencies
  52:4  FST001  [Fast]           time.sleep() in tests slows down the suite
  67:4  BHV001  [Behavioral]     MagicMock() substitutes real behavior

4 violations in 1 file
```

## Installation

```bash
pip install testdesiderata
pip install "testdesiderata[ai]"   # AI review for Writable/Inspiring desiderata
```

## Usage

```bash
testdesiderata tests/                     # lint a directory
testdesiderata --select DET,FST tests/    # only deterministic + fast rules
testdesiderata --ignore BHV tests/        # skip behavioral rules
testdesiderata --ai tests/                # include AI review
```

Exit code `0` = clean, `1` = violations. Suitable for CI.

## Configuration

```toml
[tool.testdesiderata]
select = ["DET", "FST", "ISO"]
ignore = ["BHV"]
```

CLI flags override config. Config is found by walking up from the working directory.

## Rules

| Prefix | Desideratum | What it catches |
|--------|-------------|-----------------|
| `DET` | Deterministic | `random`, `datetime.now`, `uuid4`, `os.urandom` |
| `ISO` | Isolated | `global`, env mutation, file I/O, network, DB connections |
| `FST` | Fast | `time.sleep`, polling loops |
| `AUT` | Automated | `input()`, `breakpoint()`, `pdb.set_trace()` |
| `BHV` | Behavioral | `Mock`/`MagicMock`, `@patch` |
| `STR` | Structure-insensitive | `.assert_called_with()` and related mock methods |
| `SPC` | Specific | bare/broad `except`, compound assert without message |
| `PRD` | Predictive | `pytest.skip`, `@mark.skip`, `@mark.xfail` without `strict=True` |
| `CMP` | Composable | >10 assertions or >50 lines per test |
| `RDL` | Readable | non-descriptive names, long tests without docstrings |
| `WRT` | Writable | boilerplate cost, maintenance burden *(requires `--ai`)* |
| `INS` | Inspiring | weak assertions, missing edge cases *(requires `--ai`)* |

Full rule reference: [docs/rules.md](docs/rules.md)

## Python API

```python
from testdesiderata.linter import Linter

linter = Linter()
violations = linter.lint_path(Path("tests/"))
for v in violations:
    print(v)  # tests/test_auth.py:14:4: DET001 [Deterministic] ...
```

## Slow test detection

Pass `--junit report.xml` (or let the CLI auto-detect) to flag tests exceeding `--slow` seconds (default `1.0`).

## MCP server

```bash
pip install "testdesiderata[mcp]"
claude mcp add testdesiderata -- python -m testdesiderata.mcp_server
```
