# Implementation: discriminative_tasks

feature: discriminative_tasks

**Session:** 2026-10-10 (hybrid — one agent, sequential roles)
**Spec Gate:** approved (`spec-gate.md`) → in_progress

## Batches (evidence in harness/logs/discriminative_tasks/)

| Batch | Tasks | Log |
|---|---|---|
| 1 | T1 (loader: `_expert` → level) + T2 (`--level easy\|hard\|expert` + EXTRA_FILES in the 4 runners + name validation in the loader) + T3 (by_level expert + report + `tasks_version` v3) | batch-1.log |
| 2 | T4 (3 expert python tasks) — author validation: ref OK, partial fails at the 3rd behaviour | batch-2.log |
| 3 | T5 (3 expert bash tasks) — ref OK / partials fail; lesson: `LC_NUMERIC=ca_ES.UTF-8` → decimal comma, the ref forces `LC_ALL=C` | batch-3.log |
| 4 | T6 (3 expert java tasks) — ref OK / partials fail (ledger: instance per error in the test) | batch-4.log |
| 5 | T7 (3 expert typescript tasks) — ref OK / partials fail (event_debug: stats with `max=3` before trimming) | batch-5.log |
| 6 | T8 (structural test `test_expert_tasks.py`) | batch-6.log |
| 7 | T9 (R5 smoke) + T10 (docs + traceability + gate) | smoke-r5.log + smoke-r5.md + batch-7.log |

Author validation of the 12 tasks (R3, second half): `author-validation.log`
(ref=OK, partial=fails exactly at the third behaviour). Reference, partial and
buggy solutions live in `/tmp/opencode/expert/` and are NOT committed (do not leak
them to the models). Registration in `feature_list.json` repaired in this session
(the checkpoint command had died: feature 5 was missing and `remeasure_pool` read
`in_progress` instead of `blocked`).

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_level_hard_by_id_suffix test_level_filter test_level_passes_through_with_code test_level_dropped_without_code test_none_level_is_passthrough test_expert_is_a_valid_level test_non_code_dims_get_no_level | tasks_loader.py run.py | done |
| R2 | test_code_tasks_carry_extra_files test_invalid_extra_files_rejected test_valid_extra_files_accepted test_extra_files_passthrough_from_module test_python_sees_fixture test_bash_sees_fixture test_java_helper_class_compiled test_typescript_imports_extra_module test_runner_files_win_on_collision test_missing_extra_file_fails test_data_tasks_carry_their_fixture | tasks_loader.py executors.py | done |
| R3 | test_at_least_three_expert_tasks_per_lang test_ids_end_with_expert_and_level_is_expert test_each_is_specified_and_judged test_data_tasks_carry_their_fixture test_debug_tasks_embed_the_buggy_context test_levels_are_disjoint_and_complete | tasks/code/*/*_expert.py (12 tasks) | done |
| R4 | test_by_level_folded_score_and_breakdown test_by_level_defaults_to_easy_without_key test_code_by_level_shown_when_present test_no_by_level_section_when_absent test_v3_marks_expert_tier | graders.py html_report.py config.py | done |
| R5 | test_evidence_covers_at_least_two_models test_r5_expert_gap_at_least_20_points test_evidence_only_expert_tasks | harness/specs/discriminative_tasks/smoke-r5.md (2 models, 2 tasks separate ✓/✗: log_filter_debug_expert, proc_registry_expert; gap 100) | done |
| R6 | test_weights_sum_to_one test_weights_unchanged test_non_expert_tasks_untouched | (no change: weights, dimensions and folding intact) | done |
| R7 | test_r7_retired_no_efficiency_dimension | (retired requirement: no new dimension) | done |

Content validation of the expert tasks (R3, second half: TEST_CODE fails with
partial solutions): evidence in `harness/logs/discriminative_tasks/author-validation.log`
(12/12 ref OK, 12/12 partial fails at the third behaviour, plus 4 buggy failing at the
first error). Solutions are not committed.
