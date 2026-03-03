# Rule Reference

All rule IDs, what they detect, and why.

---

## Deterministic (DET)

Tests should produce the same result every time they run.

### DET001 — random call

```python
# bad
def test_something():
    x = random.randint(1, 10)   # DET001
```

Detects calls to any `random.*` function. Use fixed seeds or inject values instead.

### DET002 — datetime.now

```python
# bad
def test_something():
    now = datetime.datetime.now()   # DET002
```

Detects `datetime.now()`, `datetime.today()`, `datetime.utcnow()`. Inject a fixed datetime instead.

### DET003 — time.time

```python
# bad
def test_something():
    t = time.time()   # DET003
```

Detects `time.time()`, `time.monotonic()`, `time.perf_counter()`, `time.process_time()`, `time.time_ns()`.

### DET004 — uuid4

```python
# bad
def test_something():
    uid = uuid.uuid4()   # DET004
```

Detects `uuid.uuid4()` and `uuid.uuid1()`. Use a fixed UUID literal in tests.

### DET005 — os.urandom

```python
# bad
def test_something():
    token = os.urandom(16)   # DET005
```

---

## Isolated (ISO)

Tests should not share state with other tests or depend on the environment.

### ISO001 — global state mutation

```python
# bad
counter = 0
def test_increments():
    global counter   # ISO001
    counter += 1
```

Detects `global` statements inside test functions.

### ISO002 — environment mutation

```python
# bad
def test_something():
    os.environ["KEY"] = "value"   # ISO002
```

Detects `os.environ` subscript assignment, `.update()`, `.pop()`, `.clear()`, `.setdefault()`, and `sys.path` mutations (`.append()`, `.insert()`, `.remove()`). Use `monkeypatch` fixture or dependency injection instead.

### ISO003 — file I/O

```python
# bad
def test_something():
    with open("data.txt") as f:   # ISO003
        data = f.read()
```

Detects `open()`, `Path.read_text()`, `Path.read_bytes()`, `Path.write_text()`, `Path.write_bytes()`. Use `tmp_path` fixture or in-memory alternatives.

### ISO004 — network call

```python
# bad
def test_something():
    r = requests.get("https://api.example.com")   # ISO004
```

Detects `requests.*`, `httpx.*`, `aiohttp.ClientSession`, `urllib.urlopen`. Use a real test server or dependency injection.

### ISO005 — database connection

```python
# bad
def test_something():
    conn = sqlite3.connect(":memory:")   # ISO005
```

Detects `sqlite3.connect()`, `psycopg2.connect()`, `pymysql.connect()`, `asyncpg.connect()`, `asyncpg.create_pool()`, `create_engine()`, `MongoClient()`. Use in-memory databases or test containers with proper setup/teardown.

---

## Fast (FST)

Tests should run in milliseconds.

### FST001 — sleep

```python
# bad
def test_something():
    time.sleep(0.1)   # FST001
```

Detects `time.sleep()` or bare `sleep()`. Use event primitives (`threading.Event`, `asyncio.Event`) instead.

### FST002 — polling loop with sleep

```python
# bad
def test_something():
    for _ in range(10):
        time.sleep(0.1)   # FST002
```

Detects for/while loops that contain a `sleep()` call. Replace busy-waiting with callbacks or condition variables.

### FST003 — slow test (timing data required)

```
tests/test_payment.py::test_checkout_flow took 2.34s (threshold: 1.0s)
```

Raised when a test's recorded runtime exceeds `--slow` (default `1.0s`). Requires JUnit XML; auto-detected from `report.xml`, `junit.xml`, `test-results.xml`, or `pytest-results.xml`.

---

## Automated (AUT)

Tests should run without human intervention.

### AUT001 — interactive input

```python
# bad
def test_something():
    name = input("enter name: ")   # AUT001
    breakpoint()                   # AUT001
```

Detects `input()` and `breakpoint()`.

### AUT002 — debugger call

```python
# bad
def test_something():
    pdb.set_trace()   # AUT002
```

Detects `pdb.set_trace()`, `pdb.post_mortem()`, `pdb.pm()`, and equivalents from `ipdb` and `pudb`.

---

## Behavioral (BHV)

Tests should test observable behavior, not implementation details.

### BHV001 — mock creation

```python
# bad
def test_something():
    m = MagicMock()   # BHV001
    m.method.return_value = 42
```

Detects `Mock()`, `MagicMock()`, `AsyncMock()`, `NonCallableMock()`, `NonCallableMagicMock()`. Replace with real implementations or simple fakes.

### BHV002 — patch decorator

```python
# bad
@patch("mymodule.MyClass")   # BHV002
def test_something(mock_cls):
    ...
```

Detects `@patch`, `@mock.patch`, `@unittest.mock.patch`, `@unittest.mock.object`. Use dependency injection so the real implementation can be swapped without patching.

---

## Structure-insensitive (STR)

Tests should remain valid across refactors that preserve behavior.

### STR001–STR006 — mock assertion methods

```python
# bad
def test_something():
    mock.assert_called_with(1, 2)       # STR001
    mock.assert_called_once_with(1, 2)  # STR002
    mock.assert_called_once()           # STR003
    mock.assert_not_called()            # STR004
    mock.assert_any_call(1)             # STR005
    mock.assert_has_calls([])           # STR006
```

These assert how a function was called, not what the system produced. Test return values and side effects instead.

---

## Specific (SPC)

Tests should pinpoint exactly what went wrong.

### SPC001 — broad exception handler

```python
# bad
def test_something():
    try:
        do_thing()
    except:           # SPC001 (bare)
        pass
    except Exception: # SPC001 (too broad)
        pass
```

Use specific exception types: `except ValueError`, `except ConnectionError`, etc.

### SPC002 — compound assert without message

```python
# bad
def test_something():
    assert x > 0 and y > 0   # SPC002

# ok
def test_something():
    assert x > 0 and y > 0, "both x and y must be positive"
```

When a compound assertion fails, the default message (`assert False`) doesn't say which condition failed. Add a message, or split into separate assertions.

---

## Predictive (PRD)

Tests should predict the failure mode before writing the code.

### PRD001 — pytest.skip in body

```python
# bad
def test_something():
    pytest.skip("not ready")   # PRD001
    assert True
```

Unconditionally skipped tests are dead coverage. Delete them or implement them.

### PRD002 — @pytest.mark.skip

```python
# bad
@pytest.mark.skip   # PRD002
def test_something():
    assert True
```

Same as PRD001 — skipped tests mask coverage gaps.

### PRD003 — xfail without strict

```python
# bad
@pytest.mark.xfail        # PRD003 — silently passes on unexpected success
def test_something():
    assert False

# ok
@pytest.mark.xfail(strict=True)   # fails loudly if the test unexpectedly passes
def test_something():
    assert False
```

Without `strict=True`, an xfail test that starts passing is marked `XPASS` and the suite still exits `0`.

---
