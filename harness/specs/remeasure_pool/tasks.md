# Tasks: remeasure_pool

- [x] T1: Pre-flight — no live servers (ports 8999/8080 free), green unittest
      suite, pool backup to `results/models/pool.pre-remeasure.jsonl`
      depends_on: (none)
      refs: R2

- [x] T2: llama batch — `python3 -m benchmark.run --models all` + ON (dual thinking_batches batch: off 10/10 + on 10/10, with restart documented in the log for early process death) (sequential, one server
      at a time) with log at `harness/logs/remeasure_pool/batch-llama.log`
      depends_on: T1
      refs: R1, R2

- [x] T3: Strata batch — `python3 -m benchmark.run --engine strata --models iq3_xxs` + ON (strata on/v3 code=0.92, exit 0, batch-strata-on.log)
      with log at `harness/logs/remeasure_pool/batch-strata.log` (only when no
      llama-server remains alive)
      depends_on: T2
      refs: R1, R2

- [x] T4: Verification — pool with single-session entries and with by_level +
      tasks_version v2; regenerate `results/report.html` and check the mixed-conditions
      banner does not appear
      depends_on: T3
      refs: R3, R4

- [x] T5: Evidence and gate — final scoreboard, ts per model and checks in
      `harness/logs/remeasure_pool/summary.log`; traceability; request Completion Gate
      depends_on: T4
      refs: R5
