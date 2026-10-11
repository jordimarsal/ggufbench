# Review — feature 2 (remeasure_pool)

**Verdict:** APPROVED (pending the human Completion Gate)

Reviewer: same agent in review mode (hybrid). This feature changes no code (only
execution + evidence): the review verifies requirements, pool state and logs.

## Requirement traceability ↔ tests

- R1: [x] Evidence: 4 logs with 10+10+1+1 models ✓, exit 0 (except restart
  documented); pool with 22 v3 rows. Capability tests: `test_upsert_keeps_both_thinking_modes`,
  `test_thinking_on_off_passthrough`, `test_table1_labels_think_and_excluded`.
  Declared deviation: v3+expert instead of v2+hard (conditions in force at measurement).
- R2: [x] Evidence: pre-batch checks (no live engine) + sequential logs without
  overlap + 0 orphans at the end. Related test: `test_ports_and_ready_timeout_per_engine`.
- R3: [x] Evidence: pool 22 rows (11 off + 11 on), one date, no legacy (in the backup).
  Declared deviation: two rows per model (one per mode), not one.
  Tests: `test_legacy_row_without_thinking_coexists_with_off`,
  `test_upsert_keeps_both_thinking_modes`.
- R4: [x] Evidence: `results/report.html` regenerated, grep "Condicions barrejades" = 0,
  badges 11+11. Tests: `test_banner_only_with_mixed_dates`,
  `test_think_badges_and_excluded_line`.
- R5: [x] Evidence: 6 logs + summary.log (scoreboard + checks).
  Test: `test_runs_filenames_distinguish_mode`.

## Task completion

- T1–T4: [x]. T5: [x] with this review (traceability 5/5 + `--all` PASS + init green).

## Checkpoints

- C1: [x] init.sh exit 0 (batch-verify.log: 187 passed, 1 skipped).
- C2: [x] on closing: single `in_progress` → will become `done`; current.md active.
- C3: [x] no code change in this feature (verified: `git status` only shows
  specs/progress/docs; pool+logs+report.html ignored; `.txt` profiles outside the repo).
- C4: [x] suite green; no new tests needed (execution feature).
- C5: [ ] open — closure pending the Gate.
- C6: [x] spec with EARS; spec deviations documented in the impl (approved spec not
  rewritten); every R<n> with evidence + related test.
- C7: [x] `audit_level: basic` — no new code means no new surface: (1) no
  secrets in committed logs (model outputs, traces and scores); (2-4) executors/
  sandbox untouched; (5) report regenerated with `_esc` intact (escape test green);
  (6-7) servers/network untouched.

## Data for the human Gate (quick read)

- OFF leads GLOBAL (MoE 0.95, gemma 0.89); ON clusters 0.71–0.83 dragged by
  think latency (up to 1707 ms) — the valid comparison is intra-mode.
- Code ON vs OFF: strong 27Bs rise when thinking (0.82→0.96, 0.87→0.95); small MoE drops
  (5 exclusions); 8B identical (0.73/0.73 — does not think even free).
- Strata: OFF 0.95 → ON 0.92 in code; HIGH does not break small dims (tools 1.00).
- Expert bites: folded code OFF 0.73–0.88 (previously 0.84–1.00 in v1).

## Verdict

**APPROVED** — I request the human Completion Gate for `remeasure_pool`.
