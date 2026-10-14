# Conventions

This document defines the project's conventions. The goal is uniformity: anyone
(or any agent) can open any file and understand its structure, naming and intent
without learning a new style.

---

## Languages

- **Code and identifiers:** English.
- **Comments, docstrings, task specs and project docs (SPEC, MILLORA):** English.
- Comments explain the **why** of a measurement decision or a trade-off;
  the *what* must be told by the code.

---

## Style Rules

- **Python 3.12, pure stdlib:** no external dependencies (no pytest, no requests, no
  pyproject). The suite runs with `python3 -m unittest discover -s ggufbench/tests -t .`
  from the workspace root (`/home/jordi/ia/llama/`), never from inside the package.
- **Format:** PEP 8, ~100 col lines, 4-space indentation. No formatter configured:
  uniformity is set by the existing code (open a module and imitate it).
- **Complexity:** short functions, early returns, no nested `try/except`. The
  `except` clauses catch explicit tuples (`_TRANSIENT` in `graders.py`), never bare.
- **Type hints:** gradual (MILLORA §D3). Required on the scoring functions
  (`report._scores`, `report._global_score`, `client.parse_timings`, `graders._args_equal`);
  optional elsewhere until `mypy` enters CI.

---

## Naming Rules

- Modules and functions: `snake_case`. Classes: `CapWords`. Constants: `UPPER_SNAKE`.
- Tests: `tests/test_<module>.py` mirroring the module; methods `test_<behavior>`.
- One concept, one name: `pool` (the entries), `run` (one execution), `task` (a task),
  `dim` (one of the 4 dimensions). No synonyms.
- Booleans read as predicates: `passed`, `excluded`, `lower_is_better`.

---

## File Structure

- **Flat package:** the modules (`run.py`, `server.py`, `client.py`, `graders.py`,
  `agent.py`, `executors.py`, `tasks_loader.py`, `report.py`, `html_report.py`,
  `token_budget.py`, `code_extract.py`, `config.py`) at the package root — no `src/`.
- **Tasks:** `tasks/<dim>/...` as constants files; `code/` and `agent/` nested per
  language. The loader skips `_prefix` and `__init__.py`.
- **Results (gitignored):** `results/models/pool.jsonl` (upsert per slug),
  `results/runs/` (append-only history), `results/token_budgets.json`,
  `results/report.html` (generated).

---

## Testing Rules

- **stdlib unittest** (no pytest in this project). Tests must not touch the GPU or the
  network: fake services (`FakeClient`), and `config.override()`-style with
  `setUp`/`tearDown` until one exists (MILLORA §D1).
- **Isolate every path a writer touches.** `report.save_result` writes the pool
  (`POOL_FILE`) **and** the receipt under `RESULTS_RUNS` (plus the agent sidecar):
  overriding only the pool drops junk receipts into the real `results/runs/` — which is
  exactly what happened until 2026-10-14. Test classes that save or run the pipeline
  override `POOL_FILE`, `RESULTS_RUNS` (and `RESULTS_MODELS` when the code reads the
  model dir) together, and `tests/test_report.py` pins the contract with a test that
  asserts the real results dir is untouched.
- Every bug fix includes the test that would have caught it.
- A test that only checks nothing throws is not a test.

---

## Commit Rules

- **Conventional Commits**, enforced by `.git/hooks/commit-msg`
  (`harness/tools/commit-msg`): `feat(engine): ...`, `fix(tools): ...`,
  `chore(harness): ...`. Granular commits: one intent per commit.
