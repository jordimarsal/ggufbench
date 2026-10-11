# Implementation: thinking_batches

feature: thinking_batches

**Session:** 2026-10-10 (hybrid — one agent, sequential roles)
**Spec Gate:** approved → in_progress

## Batches (evidence in harness/logs/thinking_batches/)

| Batch | Tasks | Log |
|---|---|---|
| 1 | T1 (`--thinking` + body kwarg + `thinking` in the result; pure `_parse_args` refactor) + T2 (pool key `(slug, thinking)` + filenames + tolerant legacy render) | batch-1.log (179 passed, 1 skipped) |
| 2 | T3 (`token_budget` keyed by `(model, thinking)` + `_schema = 2`; 16384 era ignored) + T4 (`CODE_MAX_TOKENS = 32768` + cap 1000; BODY updated, names intact) | batch-2.log (182 passed, 1 skipped) |
| 3 | T5 (THINK column in Tables 1/2/3 + ` (N excl.)` in the code score; banner intact) + T6 (`think:on/off` badge + `excluded code: N` in ranking and card; matrix intact) | batch-3.log (187 passed, 1 skipped) |
| 4 | T7 (docs SPEC/AGENTS/MILLORA + traceability 7/7 and --all PASS + review APPROVED) | batch-4.log (187 passed, 1 skipped) |

Batch 1 notes: `config.STRATA_EXTRA_BODY` generalized into `thinking_body(engine,
mode)` (test_client updated); `ServerManager` records `thinking` (the control goes
through the body, ADR-4); `mk()` in test_report omits the key when `thinking=None` (legacy rows).

Batch 2 notes: `test_scaled_timeout_applied_to_the_single_attempt` now expects
`[1000]` (the ladder is 32768: `60+32768/41×1.25 = 1059 → cap`; R2 intent intact,
the test NAME does not change for traceability). **T4 environment precondition:** 3 pool
models did not fix `-c` (they fell to `CONTEXT_FIXED=16384`, where 32768 does not fit:
Qwen3-VL-8B, Heretic-Q4_K_M, UD-Q3_K_XL) → `-c 65536` added to their `.txt`
(`models/` is outside the git repo; the change is capacity, not logits). Verified with
`build_args` (65536 on the 3; 160000 intact on UD-Q5_K_M).

Batch 3 notes: Table 1's token loop unpacked 3 values (ValueError with the new
5-tuples) — caught by the suite, fixed. A test insertion split
`test_code_by_level_shown_when_present` (stole its `expert 0%` assert) — caught
by the suite, restored. Both, evidence that the gates bite.

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_default_is_off test_off_disables_for_both_engines test_on_is_empty test_rejects_bogus test_thinking_defaults_off test_thinking_on_off_passthrough test_thinking_bogus_rejected test_thinking_recorded_and_validated test_extra_merges_into_body | config.py run.py server.py | done |
| R2 | test_upsert_keeps_both_thinking_modes test_legacy_row_without_thinking_coexists_with_off test_runs_filenames_distinguish_mode test_forget_removes_both_modes test_render_tolerates_rows_without_thinking | report.py | done |
| R3 | test_formula_floors_ceils_and_falls_back test_scaled_timeout_applied_to_the_single_attempt test_single_generous_budget_resolves_long_output test_stored_budget_still_honoured test_no_save_when_default_suffices test_keys_differ_by_thinking test_old_schema_ignored test_put_writes_schema | graders.py token_budget.py | done |
| R4 | test_table1_labels_think_and_excluded test_table2_labels_rows_with_mode test_table3_marks_mode test_code_by_level_shown_when_present test_no_by_level_section_when_absent test_banner_only_with_mixed_dates test_think_badges_and_excluded_line test_legacy_row_without_thinking_has_no_badge | report.py html_report.py | done |
| R5 | test_table1_labels_think_and_excluded test_think_badges_and_excluded_line test_legacy_row_without_thinking_has_no_badge | report.py html_report.py | done |
| R6 | test_only_touches_extra_channel test_thinking_leaves_protocol_untouched | config.py run.py | done |
| R7 | test_weights_unchanged test_weights_sum_to_one test_by_level_folded_score_and_breakdown | (no change: weights, folding and semantics intact) | done |
