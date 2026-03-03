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
