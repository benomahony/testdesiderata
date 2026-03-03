# Explanation

## Kent Beck's 12 Test Desiderata

In 2019, Kent Beck published a list of properties he wants test suites to have. They are listed in rough priority order — lower-numbered properties matter more when there is tension between them.

| # | Property | What it means |
|---|----------|---------------|
| 1 | **Isolated** | Tests do not affect each other |
| 2 | **Composable** | Tests can be run in any combination |
| 3 | **Fast** | Tests run quickly enough for tight feedback loops |
| 4 | **Inspiring** | Passing tests make you confident the code works |
| 5 | **Writable** | The cost to write a test is low |
| 6 | **Readable** | Tests communicate intent clearly |
| 7 | **Behavioral** | Tests cover behavior, not implementation |
| 8 | **Structure-insensitive** | Tests do not break on refactoring that preserves behavior |
| 9 | **Automated** | Tests run without human interaction |
| 10 | **Specific** | When a test fails, its failure points to the defect |
| 11 | **Deterministic** | Tests produce the same result every run |
| 12 | **Predictive** | A passing suite predicts a working system |

testdesiderata covers 10 of the 12 with static rules and the remaining 2 (Inspiring, Writable) via AI review.

---

## Why static analysis for test quality?

Most test quality tools require running the tests. testdesiderata works at the AST level — it reads your test files without executing them, which means:

- **No side effects** — the linter itself never touches the network, filesystem, or database
- **Fast** — 66 tests linted in 0.03s on the reference suite
- **CI-friendly** — runs before tests, can fail fast without requiring a passing suite

The tradeoff is that static analysis cannot detect runtime behavior. It cannot tell whether your mocks accurately model the real system, whether your assertions are actually meaningful given the code under test, or whether your test data covers the important edge cases. That is what the `--ai` reviewer is for.

---

## What testdesiderata cannot catch

Static analysis has limits. These problems require human judgment or AI review:

- **Weak assertions** — `assert response is not None` passes statically but tells you almost nothing
- **Wrong test data** — a test with hardcoded values that happen to pass but do not represent real usage
- **Missing coverage** — tests that pass but leave important branches untested
- **Misleading test names** — a test named `test_user_login` that actually tests password reset
- **Over-specified mocks** — mocks that technically follow the API but encode wrong assumptions

---

## Design choices

**Prefixes, not individual rule IDs for filtering.** `--select DET` enables all five deterministic rules at once. Individual rule suppression (like `# noqa: DET001`) is intentionally not supported — suppressing a violation inline hides the problem from the next reader.

**No configuration of thresholds.** The limits in CMP001 (10 assertions) and CMP002 (50 lines) are not configurable. If your codebase consistently needs higher limits, that is a signal to look at the tests themselves.

**`breakpoint()` is AUT001, not its own rule.** `breakpoint()` and `input()` are grouped together because both require a human to be watching the terminal. The distinction between them is not important for CI.
