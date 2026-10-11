# Implementation: hard_code_tier

feature: hard_code_tier

**Session:** 2026-10-09 (hybrid — one agent, sequential roles)
**Spec Gate:** approved (`spec-gate.md`) → in_progress

## Batches (evidence in harness/logs/hard_code_tier/)

| Batch | Tasks | Log |
|---|---|---|
| 1 | T1 (loader level) + T2 (--level CLI) | batch-1.log |
| 2 | T3 (by_level in graders) + T4 (tasks_version v2) | batch-2.log |
| 3 | T5 (html_report easy/hard) | batch-3.log |
| 4 | T6 (python hard) + T7 (bash hard) — author validation: ref OK, naive FAILS | batch-4.log |
| 5 | T8 (java hard) + T9 (typescript hard) — fix: the java solution is always class Solution (the executor writes Solution.java) | batch-5.log |
| 6 | T10 (structural test) + T11 (docs) + T12 (traceability + gate) | this file + init.sh |

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_level_hard_by_id_suffix test_by_level_defaults_to_easy_without_key | tasks_loader.py | done |
| R2 | test_level_passes_through_with_code test_level_dropped_without_code test_none_level_is_passthrough test_level_filter test_non_code_dims_get_no_level | tasks_loader.py run.py | done |
| R3 | test_by_level_folded_score_and_breakdown | graders.py | done |
| R4 | test_by_level_folded_score_and_breakdown test_by_level_defaults_to_easy_without_key | graders.py | done |
| R5 | test_code_by_level_shown_when_present test_no_by_level_section_when_absent | html_report.py | done |
| R6 | test_sixteen_tasks_four_per_lang test_ids_end_with_hard test_each_is_specified_and_judged test_levels_are_disjoint_and_complete | tasks/code/python tasks/code/bash tasks/code/java tasks/code/typescript | done |
| R7 | test_v3_marks_expert_tier | config.py run.py | done |
| R8 | test_non_code_dims_get_no_level test_none_level_is_passthrough test_weights_unchanged | run.py config.py graders.py | done |

Content validation of the hard tasks (R6): reference solutions OK and naive
FAILS — evidence in `harness/logs/hard_code_tier/batch-4.log` and `batch-5.log`. Reference
solutions are not committed (do not leak them to the models).
