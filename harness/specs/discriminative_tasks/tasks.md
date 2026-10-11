# Tasks: discriminative_tasks

- [x] T1: Expert level in the loader (`_expert` -> level) and `--level easy|hard|expert` + tests (evidence: harness/logs/discriminative_tasks/batch-1.log)
      depends_on: (none)
      refs: R1

- [x] T2: `EXTRA_FILES` — executors.run(…, extra_files) in the 4 runners + loader
      passthrough + plain-name validation + tests (evidence: batch-1.log)
      depends_on: (none)
      refs: R2

- [x] T3: `tasks_version = "v3"` + by_level/report with expert + tests (evidence: batch-1.log)
      depends_on: T1
      refs: R4, R6

- [x] T4: 3 expert python tasks (whole module / real-context debug / messy data) — vault_engine / metrics_debug / readings_etl; validation ref=OK partial=fails in author-validation.log, gates in batch-2.log
      depends_on: T1, T2
      refs: R3

- [x] T5: 3 expert bash tasks — num_report / log_filter_debug / access_agg; ref=OK partial=fails where expected (author-validation.log), gates in batch-3.log (lesson: LC_NUMERIC ca_ES -> decimal point forced with LC_ALL=C in ref and required in prompt)
      depends_on: T1, T2
      refs: R3

- [x] T6: 3 expert java tasks — interval_codec / ledger_debug / csv_index; ref=OK partials fall where expected (author-validation.log), gates in batch-4.log
      depends_on: T1, T2
      refs: R3

- [x] T7: 3 expert typescript tasks — proc_registry / event_debug / jsonl_agg; ref=OK partials fall where expected (author-validation.log), gates in batch-5.log
      depends_on: T1, T2
      refs: R3

- [x] T8: Structural test (12 tasks, 3 per language, multi-part, EXTRA_FILES where applicable)
      + author validation ref/partial (log in harness/logs/discriminative_tasks/)
      depends_on: T4, T5, T6, T7
      refs: R3

- [x] T9: Discrimination smoke with >= 2 real models (R5) — runs inside the
      unlocked re-measure
      depends_on: T8
      refs: R5

- [x] T10: Docs (SPEC, AGENTS.md) + traceability + harness/init.sh + request Completion
      Gate
      depends_on: T3, T9
      refs: R1, R2, R4, R6
