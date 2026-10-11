# Tasks: hard_code_tier

- [x] T1: Level support in the loader (`level` in the task dict + `load(dim, level=None)`)
      depends_on: (none)
      refs: R1, R2

- [x] T2: `--level {easy,hard}` in run.py, code-only filter, with empty-case warnings
      depends_on: T1
      refs: R2, R3

- [x] T3: `level` in the trace and `by_level` in the code result (graders) + tests
      depends_on: T1
      refs: R3, R4

- [x] T4: `tasks_version = "v2"` in new results + test
      depends_on: T1
      refs: R7

- [x] T5: Code easy/hard breakdown in the html_report model card + tests
      depends_on: T3
      refs: R5

- [x] T6: 4 hard python tasks (bug fix, operation bound, algorithm, refactor)
      depends_on: T1
      refs: R6

- [x] T7: 4 hard bash tasks (same patterns, TEST_CODE with verifiable output)
      depends_on: T1
      refs: R6

- [x] T8: 4 hard java tasks (Solution.java/Test.java, case-insensitive OK)
      depends_on: T1
      refs: R6

- [x] T9: 4 hard typescript tasks (bun, solution exported like the easy ones)
      depends_on: T1
      refs: R6

- [x] T10: Structural test of the 16 hard tasks (loadable, level=hard, 4 per
      language, non-empty TEST_CODE) — `tests/test_hard_tasks.py`
      depends_on: T6, T7, T8, T9
      refs: R6

- [x] T11: Docs: SPEC §tasks + AGENTS.md (`_hard` convention, `--level` flag,
      tasks_version v2)
      depends_on: T2
      refs: R1, R2, R7

- [x] T12: Full traceability (impl_hard_code_tier.md), check-traceability.py and
      green harness/init.sh; request Completion Gate
      depends_on: T4, T5, T10, T11
      refs: R1, R2, R3, R4, R5, R6, R7, R8
