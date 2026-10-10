# Implementació: discriminative_tasks

feature: discriminative_tasks

**Sessió:** 2026-10-10 (hybrid — un agent, rols sequencials)
**Spec Gate:** aprovat (`spec-gate.md`) → in_progress

## Batches (evidències a harness/logs/discriminative_tasks/)

| Batch | Tasques | Log |
|---|---|---|
| 1 | T1 (loader: `_expert` → level) + T2 (`--level easy\|hard\|expert` + EXTRA_FILES als 4 runners + validació de noms al loader) + T3 (by_level expert + report + `tasks_version` v3) | batch-1.log |
| 2 | T4 (3 tasques expert python) — validació d'autor: ref OK, partial falla al 3r comportament | batch-2.log |
| 3 | T5 (3 tasques expert bash) — ref OK / partials fallen; lliçó: `LC_NUMERIC=ca_ES.UTF-8` → coma decimal, el ref força `LC_ALL=C` | batch-3.log |
| 4 | T6 (3 tasques expert java) — ref OK / partials fallen (ledger: instància per error al test) | batch-4.log |
| 5 | T7 (3 tasques expert typescript) — ref OK / partials fallen (event_debug: stats amb `max=3` abans de retallar) | batch-5.log |
| 6 | T8 (test estructural `test_expert_tasks.py`) | batch-6.log |
| 7 | T9 (fum R5) + T10 (docs + traçabilitat + gate) | smoke-r5.log + smoke-r5.md + batch-7.log |

Validació d'autor de les 12 tasques (R3, segona meitat): `author-validation.log`
(ref=OK, partial=falla exactament al tercer comportament). Les solucions de referència,
parcials i buggy viuen a `/tmp/opencode/expert/` i NO es commiten (no filtrar-les als
models). Registre a `feature_list.json` reparat en aquesta sessió (la comanda del
checkpoint havia caigut: faltava la feature 5 i `remeasure_pool` figurava
`in_progress` en comptes de `blocked`).

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_level_hard_by_id_suffix test_level_filter test_level_passes_through_with_code test_level_dropped_without_code test_none_level_is_passthrough test_expert_is_a_valid_level test_non_code_dims_get_no_level | tasks_loader.py run.py | done |
| R2 | test_code_tasks_carry_extra_files test_invalid_extra_files_rejected test_valid_extra_files_accepted test_extra_files_passthrough_from_module test_python_sees_fixture test_bash_sees_fixture test_java_helper_class_compiled test_typescript_imports_extra_module test_runner_files_win_on_collision test_missing_extra_file_fails test_data_tasks_carry_their_fixture | tasks_loader.py executors.py | done |
| R3 | test_at_least_three_expert_tasks_per_lang test_ids_end_with_expert_and_level_is_expert test_each_is_specified_and_judged test_data_tasks_carry_their_fixture test_debug_tasks_embed_the_buggy_context test_levels_are_disjoint_and_complete | tasks/code/*/*_expert.py (12 tasques) | done |
| R4 | test_by_level_folded_score_and_breakdown test_by_level_defaults_to_easy_without_key test_code_by_level_shown_when_present test_no_by_level_section_when_absent test_v3_marks_expert_tier | graders.py html_report.py config.py | done |
| R5 | test_evidence_covers_at_least_two_models test_r5_expert_gap_at_least_20_points test_evidence_only_expert_tasks | harness/specs/discriminative_tasks/smoke-r5.md (2 models, 2 tasques separen ✓/✗: log_filter_debug_expert, proc_registry_expert; gap 100) | done |
| R6 | test_weights_sum_to_one test_weights_unchanged test_non_expert_tasks_untouched | (cap canvi: pesos, dimensions i plegat intactes) | done |
| R7 | test_r7_retired_no_efficiency_dimension | (requisit jubilat: cap dimensió nova) | done |

Validació de contingut de les tasques expert (R3, segona meitat: TEST_CODE falla amb
solucions parcials): evidència a `harness/logs/discriminative_tasks/author-validation.log`
(12/12 ref OK, 12/12 partial falla al tercer comportament, més 4 buggy que fallen al
primer error). Les solucions no es commiten.
