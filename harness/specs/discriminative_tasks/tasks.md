# Tasks: discriminative_tasks

- [x] T1: Nivell expert al loader (`_expert` -> level) i `--level easy|hard|expert` + tests (evidència: harness/logs/discriminative_tasks/batch-1.log)
      depends_on: (none)
      refs: R1

- [x] T2: `EXTRA_FILES` — executors.run(…, extra_files) als 4 runners + passthrough del
      loader + validació de noms plans + tests (evidència: batch-1.log)
      depends_on: (none)
      refs: R2

- [x] T3: `tasks_version = "v3"` + by_level/report amb expert + tests (evidència: batch-1.log)
      depends_on: T1
      refs: R4, R6

- [x] T4: 3 tasques expert de python (mòdul sencer / debug context real / dades lleigues) — vault_engine / metrics_debug / readings_etl; validació ref=OK partial=falla a author-validation.log, gates a batch-2.log
      depends_on: T1, T2
      refs: R3

- [x] T5: 3 tasques expert de bash — num_report / log_filter_debug / access_agg; ref=OK partial=falla on toca (author-validation.log), gates a batch-3.log (aprenentatge: LC_NUMERIC ca_ES -> punt decimal forçat amb LC_ALL=C al ref i requís al prompt)
      depends_on: T1, T2
      refs: R3

- [x] T6: 3 tasques expert de java — interval_codec / ledger_debug / csv_index; ref=OK partials cauen on toca (author-validation.log), gates a batch-4.log
      depends_on: T1, T2
      refs: R3

- [x] T7: 3 tasques expert de typescript — proc_registry / event_debug / jsonl_agg; ref=OK partials cauen on toca (author-validation.log), gates a batch-5.log
      depends_on: T1, T2
      refs: R3

- [x] T8: Test estructural (12 tasques, 3 per llengua, multi-part, EXTRA_FILES on toqui)
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
