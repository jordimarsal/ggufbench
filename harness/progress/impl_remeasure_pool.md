# Implementation: remeasure_pool

feature: remeasure_pool

**Session:** 2026-10-10 (hybrid — one agent, sequential roles)
**Spec Gate:** approved (2026-10-09) → blocked → in_progress (unlocked 2026-10-10)

## Deviations from the approved spec (declared for the Gate)

The spec was approved before the `thinking_batches` decisions and says v2/hard/one row
per model/`--models all`. The executed reality, approved by the human reviewer in later
documented decisions (`blocked.md`, gates of features 5 and 6), is:

- **R1 (v2/hard → v3/hard+expert):** the task set in force when measuring includes the
  expert level; measuring under v2 would have measured already superseded conditions.
  Overridden by human decision (Completion Gate of `discriminative_tasks`).
- **R1/R3 (one row per model → two, one per mode):** the dual think/no-think batch
  (human decision + Spec/Completion Gates of `thinking_batches`) requires keying
  by `(slug, thinking)`. "No entries from a previous condition" is satisfied: the 11
  v1 legacy rows were archived to the backup and the final pool has 22 fresh ones (11 off + 11 on).
- **T2 (`--models all` → explicit list of 10):** `all` would glob models outside the
  pool (the directory has more); the explicit list guarantees R1 ("every model
  present in the pool"). Equivalent behaviour, stricter.

## Batches (evidence in harness/logs/remeasure_pool/)

| Batch | Content | Log |
|---|---|---|
| T1 | Pre-flight: no servers, free ports, 187 passed suite, homogeneous v1 pool, Strata config, `-c 65536` on the 3 profiles, HTTP 200 kwarg probe against llama-server | preflight.log |
| T2 | llama OFF (10 models, full dims/levels, exit 0, ~31 min) + llama ON (10/10 with restart documented for early process death at 3/10) | batch-llama-off.log, batch-llama-on.log |
| T3 | Strata OFF (code 0.95) + Strata ON (code 0.92, HIGH does not break small dims), verified no orphan engine between batches | batch-strata-off.log, batch-strata-on.log |
| T4 | Pool 22 fresh rows (one date, v3, by_level with expert, recorded exclusions) + `results/report.html` without banner, badges 11+11 | summary.log (scoreboard) |
| T5 | This file + traceability + review + gate | summary.log (checks) |

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_upsert_keeps_both_thinking_modes test_thinking_on_off_passthrough test_table1_labels_think_and_excluded | batch-llama-off.log batch-llama-on.log batch-strata-off.log batch-strata-on.log (10+10+1+1 ✓, exit 0) | done |
| R2 | test_ports_and_ready_timeout_per_engine | pre-launch checks (no live engine before each batch, current.md); sequential logs, never overlapped | done |
| R3 | test_legacy_row_without_thinking_coexists_with_off test_upsert_keeps_both_thinking_modes | pool.jsonl: 22 rows (11 off + 11 on), all v3 from one date; legacy in the pre-remeasure backup | done |
| R4 | test_banner_only_with_mixed_dates test_think_badges_and_excluded_line | results/report.html regenerated: no banner, badges 11+11 | done |
| R5 | test_runs_filenames_distinguish_mode | harness/logs/remeasure_pool/ (6 logs) + summary.log | done |

Traceability note: R1-R3 are verified by **run evidence** (logs + pool inspection
in summary.log), not by unit test — the pool is gitignored and no test can depend on
it in a clean checkout. The cited IDs are the mechanical capability that makes it
possible (dual key, flag, render), all existing and green.
