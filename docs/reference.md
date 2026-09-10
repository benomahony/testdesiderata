# Reference

## CLI

```
Usage: testdesiderata [OPTIONS] PATHS...

Arguments:
  PATHS  Files or directories to lint  [required]

Options:
  -s, --select TEXT  Comma-separated rule prefixes to run (e.g. DET,FST)
  -i, --ignore TEXT  Comma-separated rule prefixes to skip (e.g. BHV)
  --junit PATH       JUnit XML for timing (auto-detected if absent)
  --slow FLOAT       Slow test threshold in seconds  [default: 1.0]
  --ai               Run AI reviewer for Writable/Inspiring desiderata
  -h, --help         Show this message and exit.
```

Auto-detected JUnit filenames: `report.xml`, `junit.xml`, `test-results.xml`, `pytest-results.xml`.

Exit codes: `0` = no violations, `1` = violations found.

---

## Config file

`[tool.testdesiderata]` in `pyproject.toml`:

| Key | Type | Description |
|-----|------|-------------|
| `select` | `list[str]` or `str` | Rule prefixes to run. All rules run if absent. |
| `ignore` | `list[str]` or `str` | Rule prefixes to skip. Nothing skipped if absent. |

```toml
[tool.testdesiderata]
select = ["DET", "FST"]
ignore = ["BHV"]
```

String form is also accepted: `select = "DET,FST"`. Config is found by walking up from the working directory; the first `pyproject.toml` with a `[tool.testdesiderata]` section wins.

---

## Suppressing a single violation

A trailing comment on the reported line suppresses it:

| Comment | Effect |
|---------|--------|
| `# noqa: DET001` | Suppresses that exact rule ID on this line |
| `# noqa: DET` | Suppresses the whole prefix (any DET rule) on this line |
| `# noqa: DET001, ISO003` | Suppresses multiple codes on this line |
| `# noqa` | Suppresses every violation on this line |

Matching is done on real comment tokens (via `tokenize`), so `noqa` appearing inside a string literal is never treated as a suppression. Suppression is per-line and only takes effect through `lint_file`/`lint_path` (and therefore the CLI) — `lint_tree` has no source text to scan, so `# noqa` has no effect there.

---

## Python API

### `Linter`

```python
from testdesiderata.linter import Linter

Linter(rules: list[Rule] | None = None)
```

Passing `rules=None` uses `ALL_RULES`. Pass a custom list to restrict which rules run.

| Method | Returns | Description |
|--------|---------|-------------|
| `lint_tree(tree, filename)` | `list[Violation]` | Lint a pre-parsed `ast.AST` |
| `lint_file(path)` | `list[Violation]` | Parse and lint a single file |
| `lint_path(path)` | `list[Violation]` | Lint a file or recursively lint a directory |

All methods return violations sorted by `(filename, line, col, rule_id)`. `lint_file` returns `[]` on `SyntaxError`. `lint_file`/`lint_path` apply `# noqa` suppression (see above); `lint_tree` does not, since it has no source text to scan.

### `Violation`

```python
@dataclass(frozen=True)
class Violation:
    filename: str
    line: int
    col: int
    rule_id: str
    desideratum: str
    message: str
```

`str(violation)` → `"filename:line:col: RULE_ID [Desideratum] message"`

### `Rule` protocol

```python
class Rule(Protocol):
    rule_id: str
    def check(self, tree: ast.AST, filename: str) -> list[Violation]: ...
```

Implement this protocol to add custom rules.

### Rule registry

```python
from testdesiderata.rules import ALL_RULES  # list[Rule]
```

Contains one instance of each built-in rule class.
