# Implementation: context_receipts

feature: context_receipts

**Session:** 2026-11-05 (hybrid — one agent, sequential roles)
**Spec Gate:** approved by the human → in_progress

## Batches (evidence in harness/logs/context_receipts/)

| Batch | Tasks | Log |
|---|---|---|
| 1 | T1 (`client.parse_usage`: usage → timings fallback → None) + T2 (`in_tokens` in the tools/code/speed trace entries, omitted on transport errors) | batch-1.log (500 tests, 0 errors, 68 skips) |
| 2 | T3 (agent per-turn `turn_in_tokens` + `session_in_tokens`; `grade_agent` writes both into the entry) + T4 (mean/median rollups per dim, over all calls across runs) | batch-2.log (506 tests, 0 errors, 68 skips) |
| 3 | T5 (`report.receipts()` + CLI `=== Context receipts (tokens sent) ===` table, '?' for legacy rows) + T6 (HTML `Context receipts` table, `miss` class; `_pack`/sort keys untouched) | batch-3.log (511 tests, 0 errors, 68 skips) |
| 4 | T7 (SPEC §4.2/§4.4/§4.7 + ADR-0011 + traceability + gates) | batch-4.log |

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_usage_prompt_tokens test_timings_fallback_without_usage test_none_when_neither_source | client.py parse_usage | done |
| R2 | test_tools_trace_carries_in_tokens test_tools_entry_without_usage_or_timings_is_none test_transport_error_entry_omits_receipt test_code_trace_carries_in_tokens_next_to_out_tokens test_code_passing_run_records_both_tokens test_speed_entry_carries_in_tokens test_speed_entry_zero_when_no_source | graders.py grade_tools grade_code grade_speed | done |
| R3 | test_turn_list_and_session_sum test_session_none_when_no_usage_anywhere test_sent_tokens_grow_with_the_re_sent_history test_agent_trace_and_session_rollups | agent.py run_agent graders.py grade_agent | done |
| R4 | test_tools_rollups_mean_and_median test_code_rollups_over_calls_even_when_tasks_are_excluded test_agent_trace_and_session_rollups | graders.py grade_tools grade_code grade_agent | done |
| R5 | test_receipts_helper_reads_the_rollups test_render_has_context_receipts_section test_render_receipts_mark_legacy_rows_with_a_question_mark test_context_receipts_section_renders_values test_context_receipts_legacy_row_renders_a_question_mark | report.py receipts html_report.py _receipt_row _sections | done |
| R6 | test_spec_documents_the_receipts_pipeline | docs/SPEC.md §4.2 §4.4 §4.7 — plus the full-suite gate harness/init.sh as the green-suite half of R6 | done |
| R7 | test_weights_unchanged test_weights_sum_to_one test_upsert_replaces_same_model test_key_ignores_the_shape_of_the_model_path | report.py _scores _key_of config.py WEIGHTS — all untouched by this feature and green: no key extension, no score-path change | done |
