# Tasks: discriminative_tasks

- [ ] T1: Nivell expert al loader (`_expert` -> level) i `--level easy|hard|expert` + tests
      depends_on: (none)
      refs: R1

- [ ] T2: `EXTRA_FILES` — executors.run(…, extra_files) als 4 runners + passthrough del
      loader + validació de noms plans + tests
      depends_on: (none)
      refs: R2

- [ ] T3: `tasks_version = "v3"` + by_level/report amb expert + tests
      depends_on: T1
      refs: R4, R6

- [ ] T4: 3 tasques expert de python (mòdul sencer / debug context real / dades lleigues)
      depends_on: T1, T2
      refs: R3

- [ ] T5: 3 tasques expert de bash
      depends_on: T1, T2
      refs: R3

- [ ] T6: 3 tasques expert de java (classe Solution, convenció ADR del bug Solution.java)
      depends_on: T1, T2
      refs: R3

- [ ] T7: 3 tasques expert de typescript
      depends_on: T1, T2
      refs: R3

- [ ] T8: Test estructural (12 tasques, 3 per llengua, multi-part, EXTRA_FILES on toqui)
      + validació d'autor ref/parcial (log a harness/logs/discriminative_tasks/)
      depends_on: T4, T5, T6, T7
      refs: R3

- [ ] T9: Smoke de discriminació amb >= 2 models reals (R5) — s'executa dins la
      re-mesura desbloquejada
      depends_on: T8
      refs: R5

- [ ] T10: Docs (SPEC, AGENTS.md) + traçabilitat + harness/init.sh + demanar Completion
      Gate
      depends_on: T3, T9
      refs: R1, R2, R4, R6
