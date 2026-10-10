# Implementació: hard_code_tier

feature: hard_code_tier

**Sessió:** 2026-10-09 (hybrid — un agent, rols sequencials)
**Spec Gate:** aprovat (`spec-gate.md`) → in_progress

## Batches (evidències a harness/logs/hard_code_tier/)

| Batch | Tasques | Log |
|---|---|---|
| 1 | T1 (loader level) + T2 (--level CLI) | batch-1.log |
| 2 | T3 (by_level a graders) + T4 (tasks_version v2) | batch-2.log |
| 3 | T5 (html_report easy/hard) | batch-3.log |
| 4 | T6 (python hard) + T7 (bash hard) — validació d'autor: ref OK, naive FALLA | batch-4.log |
| 5 | T8 (java hard) + T9 (typescript hard) — fix: la solució java és sempre class Solution (l'executor escriu Solution.java) | batch-5.log |
| 6 | T10 (test estructural) + T11 (docs) + T12 (traçabilitat + gate) | aquest fitxer + init.sh |

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

Validació de contingut de les tasques hard (R6): solucions de referència OK i ingènues
FALLA — evidència a `harness/logs/hard_code_tier/batch-4.log` i `batch-5.log`. Les
solucions de referència no es commiten (no filtrar-les als models).
