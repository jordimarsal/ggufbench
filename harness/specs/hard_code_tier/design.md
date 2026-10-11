# Design: hard_code_tier

Covers R1-R8 of `requirements.md`. Guiding principle: the hard level is **more code
tasks**, not a new dimension — the smallest possible surface.

---

## Files to create or modify

| File | Change |
|---|---|
| `tasks_loader.py` | Every task dict gains the `level` key (R1); `load(dim, level=None)` filters by level (R2) |
| `run.py` | New flag `--level {easy,hard}` applied only to code (R2); `tasks_version = "v2"` (R7) |
| `graders.py` | Code trace entries gain `level`; the code result gains `by_level` (R3, R4) |
| `tasks/code/<lang>/*_hard.py` (x16) | 4 new tasks per language, `ID` ending in `_hard` (R6) |
| `html_report.py` | Each model's conditions card shows `code easy/hard` when present (R5) |
| `docs/SPEC.md`, `AGENTS.md` | Document the `_hard` convention and the `--level` flag (R1, R2) |
| `tests/test_tasks_loader.py`, `tests/test_run_cli.py`, `tests/test_graders.py`, `tests/test_html_report.py`, `tests/test_hard_tasks.py` (new) | Tests for all requirements |

---

## Public signatures

```python
# tasks_loader.py
def load(dim: str, level: str | None = None) -> list[dict]:
    """As before; with level=("easy"|"hard") filters by the level key of the task dict.
    Code task dicts carry level: "hard" if ID ends in _hard, else "easy"."""


# graders.py  (change inside grade_code's return dict)
#   trace[i]["level"] -> "easy" | "hard"
#   result["by_level"] -> {"easy": float, "hard": float}   # only present levels

# run.py
#   ap.add_argument("--level", choices=["easy", "hard"], default=None)
#   applies the filter ONLY to the code dimension (before _limit)
#   result["tasks_version"] = "v2"
```

---

## Exceptions and error cases

| Case | Behavior | Req |
|---|---|---|
| `--level hard` and zero loadable hard tasks | Warning printed to stderr and code dimension without tasks (score 0, `excluded` not applicable) | R2 |
| `--level` given without `code` in `--dims` | Ignored with a single stderr warning | R2 |
| Task file without `ID` (loader default fallback) | `level = "easy"` | R1 |
| Old pool model without `by_level` | `html_report` shows only the aggregate score, no easy/hard section | R5 |
| Hard task with TEST_CODE that does not compile/run | The same code exclusion mechanics (CODE_LADDER, transient) — no special treatment | R3 |

---

## Discarded alternatives

1. **Sub-dimensions `code_easy`/`code_hard` with their own weights** — changes GLOBAL and
   would break pool comparability: discarded (user decision: folded).
2. **Separate runs with a `-hard` slug** — doubles re-measure time and splits the
   scoreboard in two: discarded.
3. **Level as a directory (`tasks/code/hard/<lang>/`)** — the nesting convention is
   per-language and the loader is single-level; the `_hard` ID suffix keeps "one file =
   one task" and makes the filter trivial: discarded.
4. **Not bumping `tasks_version`** — the pool could not tell pre/post conditions apart
   (MILLORA §C7): discarded.
5. **Reference solution inside each hard task to unit-test it** — would put the solution
   within reach of the models (PROMPT and TEST_CODE are data some servers log); hard-task
   validation is manual at creation + a structural loader test: discarded.

---

## Hard tasks: content criterion (R6)

Per language, one per pattern — the naive fails by design:

1. **Subtle bug fix** (off-by-one, mutability, simple race condition).
2. **Optimization with a max-operations/time test** (TEST_CODE includes a bound).
3. **Implementation of a specified non-trivial algorithm** (parsing, state, memoization).
4. **Refactor with behavior-pinning tests** (given API, non-negotiable).

Each file: `ID = "<name>_hard"`, `PROMPT` in Catalan, self-contained `TEST_CODE` that
prints `OK` only if everything passes (the executors' current mechanics).