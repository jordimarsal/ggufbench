# Tasks: timeout_scaling

- [x] T1: `code_timeout(budget, gen_tps)` + `grade_code(gen_tps=...)` with per-attempt
      timeout + formula tests (floor, ceiling, no tps) and received-timeout test on the fake
      depends_on: (none)
      refs: R1, R2, R3, R5

- [x] T2: run.py passes the speed dimension's gen_tps to grade_code + test
      depends_on: T1
      refs: R1, R2

- [x] T3: ADR-0001 (decision artifact, R4 retired: not testable) + validation
      (suite + init.sh) + traceability
      depends_on: T1, T2
      refs: R1, R2, R5
