# Tutorial: Lint your first test file

This tutorial walks you through installing testdesiderata, running it on a test file that has problems, interpreting the output, fixing the violations, and confirming a clean result.

## 1. Install

```bash
pip install testdesiderata
```

## 2. Create a test file to lint

Save this as `tests/test_example.py`:

```python
import random
import time
from unittest.mock import MagicMock

def test_x():
    r = random.randint(1, 100)
    time.sleep(0.1)
    m = MagicMock()
    assert r > 0
```

This file has four problems we will find and fix.

## 3. Run the linter

```bash
testdesiderata tests/test_example.py
```

Output:

```
tests/test_example.py
  1:0  RDL001  [Readable]        'test_x' is non-descriptive: use a name that describes the expected behavior
  6:4  DET001  [Deterministic]   random.randint() produces non-deterministic results
  7:4  FST001  [Fast]            time.sleep() in tests slows down the suite
  8:4  BHV001  [Behavioral]      MagicMock() substitutes real behavior

4 violations in 1 file
```

The format is `file:line:col  RULE_ID  [Desideratum]  message`.

## 4. Fix the violations

```python
def test_random_value_is_positive():          # RDL001 fixed: descriptive name
    r = 42                                    # DET001 fixed: fixed value
    assert r > 0
```

- **RDL001**: rename `test_x` to something that describes the expected behavior
- **DET001**: replace `random.randint()` with a fixed value
- **FST001**: remove `time.sleep()` — it was not doing anything useful here
- **BHV001**: remove the mock — we were not asserting anything about it

## 5. Run again

```bash
testdesiderata tests/test_example.py
```

```
✓ No violations found
```

Exit code is `0`. Your test file is now clean.

## Next steps

- [How-to guides](how-to.md) — configure testdesiderata, add it to CI, filter rules
- [Rule reference](rules.md) — detailed explanation of every rule
- [Explanation](explanation.md) — the theory behind the 12 desiderata
