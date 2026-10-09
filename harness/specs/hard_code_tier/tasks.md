# Tasks: hard_code_tier

- [x] T1: Suport de nivell al loader (`level` al task dict + `load(dim, level=None)`)
      depends_on: (none)
      refs: R1, R2

- [x] T2: `--level {easy,hard}` a run.py, filtre només code, amb avisos de cas buit
      depends_on: T1
      refs: R2, R3

- [x] T3: `level` a la traça i `by_level` al resultat de code (graders) + tests
      depends_on: T1
      refs: R3, R4

- [x] T4: `tasks_version = "v2"` als resultats nous + test
      depends_on: T1
      refs: R7

- [x] T5: Desglossament code easy/hard a la fitxa de model d'html_report + tests
      depends_on: T3
      refs: R5

- [x] T6: 4 tasques hard de python (fix-bug, cota d'operacions, algorisme, refactor)
      depends_on: T1
      refs: R6

- [x] T7: 4 tasques hard de bash (mateixos patrons, TEST_CODE amb sortida verificable)
      depends_on: T1
      refs: R6

- [x] T8: 4 tasques hard de java (Solution.java/Test.java, case-insensitive OK)
      depends_on: T1
      refs: R6

- [x] T9: 4 tasques hard de typescript (bun, export de la solució com les easy)
      depends_on: T1
      refs: R6

- [x] T10: Test estructural de les 16 tasques hard (carregables, level=hard, 4 per
      llengua, TEST_CODE no buit) — `tests/test_hard_tasks.py`
      depends_on: T6, T7, T8, T9
      refs: R6

- [x] T11: Docs: SPEC §tasques + AGENTS.md (convenció `_hard`, flag `--level`,
      tasks_version v2)
      depends_on: T2
      refs: R1, R2, R7

- [x] T12: Traçabilitat completa (impl_hard_code_tier.md), check-traceability.py i
      harness/init.sh verd; demanar Completion Gate
      depends_on: T4, T5, T10, T11
      refs: R1, R2, R3, R4, R5, R6, R7, R8
