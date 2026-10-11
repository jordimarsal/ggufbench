# Design: discriminative_tasks

Covers R1-R6. The expert level reuses all the hard-level machinery
(`_hard`→`_expert`, `--level`, `by_level`); the genuinely new piece is `EXTRA_FILES`
(R2) — multi-file support in the code sandbox.

---

## Files to create or modify

| File | Change |
|---|---|
| `tasks_loader.py` | The level map gains `_expert` → `"expert"`; every code task dict gains `extra_files` (empty dict default) |
| `run.py` | `--level` choices += `expert`; `tasks_version = "v3"` |
| `executors.py` | `run(lang, solution_code, test_code, timeout=30, extra_files=None)`: writes `extra_files` to the tempdir before solution+test (all 4 runners) |
| `graders.py` | `grade_code` passes `t.get("extra_files")` to `executors.run`; `by_level` already generic (new keys for free) |
| `tasks/code/<lang>/*_expert.py` (x12) | 3 tasks per language (R3) |
| `html_report.py` | `by_level` already rendered generically — verify expert shows up (test) |
| `docs/SPEC.md`, `AGENTS.md` | `_expert` convention, `--level expert`, tasks_version v3 |
| `tests/` | loader/--level/executors-extra-files/by_level/html/structure (hard_code_tier pattern) |

---

## Public signatures

```python
# executors.py
def run(lang: str, solution_code, test_code, timeout: int = 30,
        extra_files: dict[str, str] | None = None) -> dict: ...

# tasks_loader.py  (code task dict)
#   {..., "level": "easy|hard|expert", "extra_files": dict[str, str]}
```

---

## Exceptions and error cases

| Case | Behavior | Req |
|---|---|---|
| `--level expert` with no expert tasks (old repo) | Warning to stderr and dimension without tasks (hard pattern) | R1 |
| `EXTRA_FILES` with a path containing `..` or absolute | Rejected at task load (loader validates dict keys, never paths) — the sandbox writes only plain names | R2 |
| extra_file vs solution/test collision | `solution.*`/`test_*` always win (the extra cannot be named like that: validated at loader) | R2 |
| Expert task partially solved by a model | Multi-part TEST_CODE → fails (never excluded): partial-solution resistance is the quality criterion | R3 |

---

## Discarded alternatives

1. **Raise the weight of code** — hides the lack of discrimination, does not solve it: discarded.
2. **Expert level in the agent (bigger repos, more turns)** — valuable but it is another
   dimension and another sandbox: separate feature (stays in MILLORA §C4).
3. **Score token efficiency** — already recorded (`out_tokens`); scoring it would be
   a new dimension (R7 retired): discarded.
4. **Tasks with non-deterministic output** (creativity, design) — not verifiable with
   TEST_CODE: contradicts the verifiable data-as-code principle: discarded.

---

## Expert content criterion (R3)

Per language, 3 patterns — all multi-part and with provided context:

1. **Whole module**: implement 2-3 coordinated classes/functions (~80-150 lines of
   expected solution) with TEST_CODE testing the three pieces and their interactions.
2. **Debugging over real context**: a ~100-line file with 3 subtle bugs
   (off-by-one, aliasing, shared state) embedded in PROMPT or EXTRA_FILES; the test
   fails with any of the three unfixed.
3. **Data + robustness**: process a messy data file (EXTRA_FILES: CSV/logs with edge
   cases, quotes, partially valid lines) with a strict output contract.

Partial-solution resistance is the acceptance criterion: each task is validated
with the reference solution (OK) and with solutions solving only 2 of 3 parts
(FAILS) before committing it.
