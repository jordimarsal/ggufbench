# Review — feature context_receipts (id 9)

**Verdict:** APPROVED (hybrid in-session review mode; the human Completion Gate
remains pending — this file does not close the feature)

**Date:** 2026-11-05 · **Reviewer:** in-session agent (review mode, AGENTS.md §4)

## Requirement traceability ↔ tests

- R1: [x] `test_usage_prompt_tokens`, `test_timings_fallback_without_usage`,
  `test_none_when_neither_source` (tests/test_client.py — hit, fallback, absent)
- R2: [x] `test_tools_trace_carries_in_tokens`,
  `test_tools_entry_without_usage_or_timings_is_none`,
  `test_transport_error_entry_omits_receipt`,
  `test_code_trace_carries_in_tokens_next_to_out_tokens`,
  `test_code_passing_run_records_both_tokens` (sandbox-guarded, runs on the bench
  host), `test_speed_entry_carries_in_tokens`, `test_speed_entry_zero_when_no_source`
- R3: [x] `test_turn_list_and_session_sum`, `test_session_none_when_no_usage_anywhere`,
  `test_sent_tokens_grow_with_the_re_sent_history`,
  `test_agent_trace_and_session_rollups` (executor mocked: the receipt contract,
  not the sandbox, is under test — coverage on every host)
- R4: [x] `test_tools_rollups_mean_and_median`,
  `test_code_rollups_over_calls_even_when_tasks_are_excluded`,
  `test_agent_trace_and_session_rollups`
- R5: [x] `test_receipts_helper_reads_the_rollups`,
  `test_render_has_context_receipts_section`,
  `test_render_receipts_mark_legacy_rows_with_a_question_mark`,
  `test_context_receipts_section_renders_values`,
  `test_context_receipts_legacy_row_renders_a_question_mark`
- R6: [x] `test_spec_documents_the_receipts_pipeline` (SPEC §4.7 names parse_usage,
  session_in_tokens, ADR-0011) + full-suite gate green (batch-4.log, 512 tests)
- R7: [x] `test_weights_unchanged`, `test_weights_sum_to_one`,
  `test_upsert_replaces_same_model`, `test_key_ignores_the_shape_of_the_model_path`
  — untouched by the feature and green (no pool-key extension, no score-path edit;
  `_scores` byte-identical, receipts live in a separate `report.receipts()` seam)

Traceability script: `harness/specs/context_receipts/review.md` — **7/7 PASS**.

## Task completion

- T1–T7: [x] all ticked, each with its batch log under `harness/logs/context_receipts/`.

## Gates

- `harness/init.sh`: **exit 0** — 512 tests, 0 errors, 68 skips (platform: sandbox/
  GPU-dependent classes skip on this macOS dev host, per the suite's own guards;
  the Linux bench host runs them).
- `python3 harness/tools/check-traceability.py --all`: context_receipts 7/7. Two
  PRE-EXISTING gaps in old features (`discriminative_tasks` R4,
  `hard_code_tier` R6/R7: identifiers `test_v3_marks_expert_tier`,
  `test_sixteen_tasks_four_per_lang` were removed by the v5 task-suite rework,
  commit `d0d05a8`). Out of scope here; flagged for portfolio hygiene.

## Conventions & architecture walk

- stdlib only, no new dependencies (agent.py's `from . import client as C` is an
  intra-package import; no cycle: client imports config only).
- Naming: `parse_usage`, `receipts`, `avg/median_in_tokens`,
  `session_in_tokens` — one concept, one name; booleans/predicates untouched.
- Comments explain the why (re-send growth, calls-not-tasks rollup rule, '?'
  tolerance); type hints on the new public functions (`parse_usage`, `receipts`).
- HTML: names escaped with `_esc`, receipt cells are formatted floats, no new
  script, no external resources (R12 report_polish intact —
  `test_context_receipts_legacy_row_renders_a_question_mark` asserts the miss style).

## Security audit (audit_level: basic — manual confirmation)

- [x] No secret/token committed (docs + code + tests only).
- [x] No new `subprocess` call in this feature (parse/receipt work is pure);
      the pre-batch executors fix still routes everything through `_safe_run`.
- [x] Model code still only runs in the executors sandbox (unchanged).
- [x] No `eval`/`exec` introduced (`parse_usage` is arithmetic on the response dict).
- [x] Generated HTML: pool text escaped, numeric cells only, self-contained page.
- [x] Server binding untouched (127.0.0.1).
- [x] No `curl | sh` added.

## Checkpoints (C1–C7)

- C1: [x] base files present; `harness/init.sh` exit 0.
- C2: [x] exactly one `in_progress` (context_receipts); `current.md` describes this session.
- C3: [x] flat package respected; no debug prints, no context-free TODOs added.
- C4: [x] tests per touched module (client/graders/agent/report/html_report all extended); all green.
- C5: [ ] session closure (history move) happens AT the Completion Gate, not before.
- C6: [x] spec folder complete; EARS requirements; every R has ≥1 concrete test; tasks all [x].
- C7: [x] basic audit confirmed manually above; no findings above threshold.

## Required changes

None for this feature. (Portfolio note: refresh the stale test identifiers in the
`discriminative_tasks` / `hard_code_tier` impl tables at the human's discretion —
pre-existing, unrelated to context_receipts.)
