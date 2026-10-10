# Review — feature 6 (thinking_batches)

**Verdict:** APPROVED (pendent del Completion Gate humà)

Revisor: mateix agent en mode review (hybrid). Comandes re-executades:
`check-traceability.py --feature thinking_batches` → 7/7 PASS; `--all` → PASS;
`harness/init.sh` → verd (`batch-4.log`: 187 passed, 1 skipped).

## Requirement traceability ↔ tests

- R1: [x] `test_default_is_off`, `test_off_disables_for_both_engines`,
  `test_on_is_empty`, `test_rejects_bogus` (cos per mode i motor + validació),
  `test_thinking_defaults_off` / `test_thinking_on_off_passthrough` /
  `test_thinking_bogus_rejected` (CLI pur via `_parse_args`, sense GPU),
  `test_thinking_recorded_and_validated` (ServerManager registra),
  `test_extra_merges_into_body` (el kwarg arriba al cos enviat).
- R2: [x] `test_upsert_keeps_both_thinking_modes` (conviuen; re-run substitueix),
  `test_legacy_row_without_thinking_coexists_with_off` (`(slug,None)`≠`(slug,off)`),
  `test_runs_filenames_distinguish_mode` (`-on`/`-off`),
  `test_forget_removes_both_modes`,
  `test_render_tolerates_rows_without_thinking`,
  `test_keys_differ_by_thinking` (budgets independents per mode).
- R3: [x] `test_formula_floors_ceils_and_falls_back` (COS: sostre 1000),
  `test_scaled_timeout_applied_to_the_single_attempt` (COS: `[1000]` amb ladder 32768;
  NOM intacte), `test_single_generous_budget_resolves_long_output` /
  `test_stored_budget_still_honoured` / `test_no_save_when_default_suffices` (ladder
  únic), `test_old_schema_ignored` / `test_put_writes_schema` (era 16384 invalidada).
- R4: [x] `test_table1_labels_think_and_excluded` (asserts per fila),
  `test_table2_labels_rows_with_mode`, `test_table3_marks_mode`,
  `test_code_by_level_shown_when_present` / `test_no_by_level_section_when_absent`
  (intactes), `test_banner_only_with_mixed_dates` (banner sense canvis),
  `test_think_badges_and_excluded_line`,
  `test_legacy_row_without_thinking_has_no_badge`.
- R5: [x] `test_table1_labels_think_and_excluded` (`100% (2 excl.)`),
  `test_think_badges_and_excluded_line` + legacy (`excloses code: 0`).
- R6: [x] `test_only_touches_extra_channel` (el dict només porta el kwarg),
  `test_thinking_leaves_protocol_untouched` (dims/langs/levels idèntics on/off).
- R7: [x] `test_weights_unchanged`, `test_weights_sum_to_one`,
  `test_by_level_folded_score_and_breakdown` (pesos i plegat intactes).

## Task completion

- T1–T6: [x] (batches 1–3, verds). T7: [x] (`batch-4.log` verd + aquest review).

## Checkpoints

- C1: [x] fitxers base + docs presents; init.sh exit 0 (batch-4).
- C2: [x] una sola `in_progress` (feature 6); `done` amb tests verds; current.md actiu.
- C3: [x] paquet pla, zero dependències noves; cap print/TODO als `.py` commitejats
  (grep, vegeu batch-4); comentaris en català, identificadors en anglès.
- C4: [x] cada mòdul tocat té test (config, run, server, report, html_report,
  token_budget, graders, client); suite verda.
- C5: [ ] obert — tancament pendent del Gate.
- C6: [x] spec de 3 fitxers, EARS estricte ("SHALL"); cada R<n> amb test llegit
  (no només nom: cossos verificats un per un a dalt).
- C7: [x] `audit_level: basic` — checklist confirmat: (1) cap secret (codi + 3
  perfils `.txt` amb només flags); (2) cap `subprocess` nou; (3) codi del model
  confinat al sandbox (intacte); (4) cap `eval`/`exec` (intacte); (5) HTML amb
  `_esc` al badge de mode i enters als recomptes (test d'escapament verd);
  (6) 127.0.0.1 (intacte); (7) cap `curl|sh` nou.

## Observacions (no bloquegen; per al Gate humà)

1. **Perfils fora del git:** els 3 `-c 65536` viuen a `models/*.txt` (fora del repo).
   Condició d'entorn documentada a l'impl + als mateixos `.txt`; la re-mesura els
   necessita. Si es reinstal·la l'entorn, cal re-aplicar-los.
2. **El valor 32768 no va estampat per fila:** queda fixat per era (v3 + aquesta
   feature + git log). Acceptat: el pool es re-mesura sencer i `token_budgets.json`
   porta `_schema = 2`.
3. **Neteja feta pel camí:** la taula d'impl citava 3 IDs inexistents (infix
   `thinking_body_` que els tests no tenen) — el propi check la va tombar i s'ha
   corregit la taula, no els tests.
4. **Cost GPU:** el doble batch (~2×) cau a `remeasure_pool`, no aquí (cap run amb
   GPU en aquesta feature: tota la verificació és sense GPU per disseny).

## Veredicte

**APPROVED** — demano el Completion Gate humà per a `thinking_batches`. Després del
Gate: `remeasure_pool` → `in_progress` i doble re-mesura (off primer, on després;
mai els dos motors alhora).
