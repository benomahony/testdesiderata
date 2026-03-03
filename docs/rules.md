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
