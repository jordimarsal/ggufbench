# Implementació: thinking_batches

feature: thinking_batches

**Sessió:** 2026-10-10 (hybrid — un agent, rols sequencials)
**Spec Gate:** aprovat → in_progress

## Batches (evidències a harness/logs/thinking_batches/)

| Batch | Tasques | Log |
|---|---|---|
| 1 | T1 (`--thinking` + kwarg + `thinking` al resultat; refactor `_parse_args` pur) + T2 (clau de pool `(slug, thinking)` + filenames + render tolerant legacy) | batch-1.log (179 passed, 1 skipped) |
| 2 | T3 (`token_budget` clavat per `(model, thinking)` + `_schema = 2`; era 16384 ignorada) + T4 (`CODE_MAX_TOKENS = 32768` + cap 1000; COS actualitzat, noms intactes) | batch-2.log (182 passed, 1 skipped) |
| 3 | T5 (columna THINK a Taules 1/2/3 + ` (N excl.)` al score de code; banner intacte) + T6 (badge `think:on/off` + `excloses code: N` a ranking i targeta; matriu intacta) | batch-3.log (187 passed, 1 skipped) |
| 4 | T7 (docs SPEC/AGENTS/MILLORA + traçabilitat 7/7 i --all PASS + review APPROVED) | batch-4.log (187 passed, 1 skipped) |

Notes de batch 1: `config.STRATA_EXTRA_BODY` generalitzada a `thinking_body(engine,
mode)` (test_client actualitzat); `ServerManager` registra `thinking` (el control va
pel cos, ADR-4); `mk()` de test_report omet la clau quan `thinking=None` (files legacy).

Notes de batch 2: `test_scaled_timeout_applied_to_the_single_attempt` ara espera
`[1000]` (el ladder és 32768: `60+32768/41×1.25 = 1059 → cap`; la intenció R2 intacta,
el NOM del test no canvia per traçabilitat). **Precondició d'entorn T4:** 3 models del
pool no fixaven `-c` (queien a `CONTEXT_FIXED=16384`, on 32768 no hi cap:
Qwen3-VL-8B, Heretic-Q4_K_M, UD-Q3_K_XL) → `-c 65536` afegit als seus `.txt`
(`models/` és fora del repo git; el canvi és capacitat, no logits). Verificat amb
`build_args` (65536 als 3; 160000 intacte al UD-Q5_K_M).

Notes de batch 3: el bucle de tokens de Taula 1 desempaquetava 3 (ValueError amb les
noves tuples de 5) — detectat per la suite, arreglat. Una inserció de test va partir
`test_code_by_level_shown_when_present` (li va robar l'assert `expert 0%`) — detectat
per la suite, restaurat. Totes dues, evidència que els gates mosseguen.
`[1000]` (el ladder és 32768: `60+32768/41×1.25 = 1059 → cap`; la intenció R2 intacta,
el NOM del test no canvia per traçabilitat). **Precondició d'entorn T4:** 3 models del
pool no fixaven `-c` (queien a `CONTEXT_FIXED=16384`, on 32768 no hi cap:
Qwen3-VL-8B, Heretic-Q4_K_M, UD-Q3_K_XL) → `-c 65536` afegit als seus `.txt`
(`models/` és fora del repo git; el canvi és capacitat, no logits). Verificat amb
`build_args` (65536 als 3; 160000 intacte al UD-Q5_K_M).

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_default_is_off test_off_disables_for_both_engines test_on_is_empty test_rejects_bogus test_thinking_defaults_off test_thinking_on_off_passthrough test_thinking_bogus_rejected test_thinking_recorded_and_validated test_extra_merges_into_body | config.py run.py server.py | done |
| R2 | test_upsert_keeps_both_thinking_modes test_legacy_row_without_thinking_coexists_with_off test_runs_filenames_distinguish_mode test_forget_removes_both_modes test_render_tolerates_rows_without_thinking | report.py | done |
| R3 | test_formula_floors_ceils_and_falls_back test_scaled_timeout_applied_to_the_single_attempt test_single_generous_budget_resolves_long_output test_stored_budget_still_honoured test_no_save_when_default_suffices test_keys_differ_by_thinking test_old_schema_ignored test_put_writes_schema | graders.py token_budget.py | done |
| R4 | test_table1_labels_think_and_excluded test_table2_labels_rows_with_mode test_table3_marks_mode test_code_by_level_shown_when_present test_no_by_level_section_when_absent test_banner_only_with_mixed_dates test_think_badges_and_excluded_line test_legacy_row_without_thinking_has_no_badge | report.py html_report.py | done |
| R5 | test_table1_labels_think_and_excluded test_think_badges_and_excluded_line test_legacy_row_without_thinking_has_no_badge | report.py html_report.py | done |
| R6 | test_only_touches_extra_channel test_thinking_leaves_protocol_untouched | config.py run.py | done |
| R7 | test_weights_unchanged test_weights_sum_to_one test_by_level_folded_score_and_breakdown | (cap canvi: pesos, plegat i semàntica intactes) | done |
