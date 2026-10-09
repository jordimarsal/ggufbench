# Tasks: timeout_scaling

- [x] T1: `code_timeout(budget, gen_tps)` + `grade_code(gen_tps=...)` amb timeout per
      intent + tests de fórmula (pis, sostre, sense tps) i de timeout rebut pel fake
      depends_on: (none)
      refs: R1, R2, R3, R5

- [x] T2: run.py passa el gen_tps de la dimensió speed a grade_code + test
      depends_on: T1
      refs: R1, R2

- [x] T3: ADR-0001 (artefacte de decisió, R4 jubilada: no testable) + validació
      (suite + init.sh) + traçabilitat
      depends_on: T1, T2
      refs: R1, R2, R5
