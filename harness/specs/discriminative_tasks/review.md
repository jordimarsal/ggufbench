# Review — feature 5 (discriminative_tasks)

**Verdict:** APPROVED (pendent del Completion Gate humà)

Revisor: mateix agent en mode review (hybrid). Comandes re-executades, no afirmacions
del xat: `check-traceability.py --feature discriminative_tasks` → 7/7 PASS;
`--all` → PASS (després de remapejar 3 IDs obsolets, vegeu §4);
`harness/init.sh` → verd (`batch-7.log`).

## Requirement traceability ↔ tests

- R1: [x] `test_level_hard_by_id_suffix` (sufix `_expert` → level expert),
  `test_level_filter` (filtre `level="expert"` inclou les 12 reals, cap easy s'hi cola),
  `test_level_passes_through_with_code` / `test_level_dropped_without_code` /
  `test_none_level_is_passthrough` / `test_expert_is_a_valid_level` (`--level` només
  afecta code; `expert` parseja, `bogus` mor), `test_non_code_dims_get_no_level`.
- R2: [x] `test_code_tasks_carry_extra_files` (clau `extra_files: dict` a tota task de
  code; `readings_etl_expert` porta `readings.csv`; `bubble_sort` porta `{}`),
  `test_invalid_extra_files_rejected` (subrutes, absoluts, `..`, `solution*`, `test*`,
  buits), `test_valid_extra_files_accepted`, `test_extra_files_passthrough_from_module`,
  `test_python_sees_fixture` / `test_bash_sees_fixture` /
  `test_java_helper_class_compiled` / `test_typescript_imports_extra_module` (els 4
  runners escriuen els extras ABANS i els fitxers del runner guanyen en col·lisió:
  `test_runner_files_win_on_collision`), `test_missing_extra_file_fails`,
  `test_data_tasks_carry_their_fixture` (les 4 tasques de dades porten el fixture que
  el TEST_CODE llegeix).
- R3: [x] Estructura: `test_at_least_three_expert_tasks_per_lang` (≥3 × 4 llengües),
  `test_ids_end_with_expert_and_level_is_expert`, `test_each_is_specified_and_judged`,
  `test_debug_tasks_embed_the_buggy_context` (les 4 de debug porten el codi defectuós
  al PROMPT). Contingut (multi-part + TEST_CODE que tomba parcials): evidència
  `harness/logs/discriminative_tasks/author-validation.log` — 12/12 ref PASS, 12/12
  partial FAIL exactament al tercer comportament (+ 4 buggy que fallen al primer
  error). Les solucions viuen a `/tmp/opencode/expert/` i no es commiten.
- R4: [x] `test_by_level_folded_score_and_breakdown` (score plegat amb mateix pes per
  tasca + desglossament per nivell), `test_by_level_defaults_to_easy_without_key`,
  `test_code_by_level_shown_when_present` / `test_no_by_level_section_when_absent`
  (report), `test_v3_marks_expert_tier` (`TASKS_VERSION == "v3"`).
- R5: [x] `test_evidence_covers_at_least_two_models`,
  `test_r5_expert_gap_at_least_20_points`, `test_evidence_only_expert_tasks` sobre
  `harness/specs/discriminative_tasks/smoke-r5.md` (generat de `smoke-r5.log` amb
  `/tmp/opencode/extract_r5.py`): 2 models, 2 tasques separen ✓/✗
  (`log_filter_debug_expert`, `proc_registry_expert`), gap 100 ≥ 20. Les 2
  separacions són pass/fail reals (cap depèn d'exclusions). Pool restaurat a
  `pool.pre-remeasure.jsonl` després del fum (homogeni v1, verificat amb `diff`).
- R6: [x] `test_weights_sum_to_one`, `test_weights_unchanged` (pesos intactes),
  `test_non_expert_tasks_untouched` (`bubble_sort`/`fibonacci` easy intactes). Cap
  canvi a altres dimensions ni al plegat (el score segueix `sum/len` sobre scored).
- R7 (retired): [x] `test_r7_retired_no_efficiency_dimension` (els pesos són
  exactament les 4 dimensions; l'eficiència resta mètrica `out_tokens`, no dimensió).

## Task completion

- T1–T8: [x] (batches 1–6, tots verds). T9: [x] (fum R5 + `smoke-r5.md`). T10: [x]
  (docs + traçabilitat + `batch-7.log` verd + aquest review).

## Checkpoints

- C1: [x] AGENTS.md + init.sh + feature_list.json + current.md presents; docs
  architecture/conventions/verification presents; init.sh exit 0.
- C2: [x] Una sola feature `in_progress` (feature 5; remeasure_pool `blocked`);
  features `done` amb tests verds (`--all` PASS); current.md descriu la sessió activa.
- C3: [x] Paquet pla (sense `src/`); cap print de debug ni TODO sense context als
  fitxers commitejats (grep als `.py` canviats: només asserts i TEST_CODE amb `echo`,
  que és codi de test per disseny).
- C4: [x] Tot comportament nou té test (loader, CLI, executors, graders, config,
  estructural, R5, R7); suite verda.
- C5: [ ] obert — tancament de sessió pendent del Gate (history.md, neteja).
- C6: [x] Spec de 3 fitxers + EARS ("shall" a R1–R6); totes les tasques [x]; cada R<n>
  cobert per test concret (llegits els cossos, no només els noms).
- C7: [x] `audit_level: basic` — checklist de `docs/verification.md` confirmat:
  (1) cap secret als fitxers nous (fixtures CSV/log, codi, docs); (2) cap `subprocess`
  nou (els runners passen per `_safe_run` amb timeout, sense canvis); (3) el codi del
  model només s'executa al sandbox d'`executors.py` (els EXTRA_FILES s'escriuen al
  mateix tempdir amb els mateixos límits; java compila tots els `.java` dins el
  sandbox); (4) cap `eval`/`exec` de sortida del model (extracció textual, intacta);
  (5) l'HTML escapa (`_esc`, tests de self-contenció intactes; no toco
  `html_report.py`); (6) servidors a 127.0.0.1 (intacte); (7) cap `curl|sh` nou.

## Observacions (no bloquegen; per al Gate humà)

1. **D6 (nou, a MILLORA.md):** `--dims` sense `speed` degrada `code_timeout` a 90 s
   fixes → el primer intent del fum va excloure 4/4 tasques per timeout del rellotge
   (`smoke-r5-attempt1.log`). La re-mesura completa no hi cau (`speed` corre primer).
   Proposta registrada (fallback des de `token_budget`/pool), no implementada aquí.
2. **Sostre de tokens al fum:** el 27B va exhaurir `out_tokens=16384` amb text buit en
   7/12 tasques (hipòtesi: `<think>` del template Qwen3 a `reasoning_content`, fora de
   `content`; el client és pass-through fidel). El harness ho exclou (no ho compta),
   que és l'honestedat dissenyada — però afalaga el score plegat (1.00 sobre 5
   puntuables). Observació per a la re-mesura, no defecte d'aquesta feature (R6
   prohibeix tocar el plegat).
3. **Remaps d'IDs en features `done` (§4):** el meu commit `aabff88` havia renombrat 2
   tests (`test_easy_and_hard_are_disjoint_and_complete` →
   `test_levels_are_disjoint_and_complete`, que verifica un superconjunt;
   `test_v2_marks_hard_tier` → `test_v3_marks_expert_tier`, mateix mecanisme amb v3⊃v2)
   i va trencar la traçabilitat de `hard_code_tier`; més un ID obsolet de la feature 4
   (`test_ladder_uses_scaled_timeouts` → `test_scaled_timeout_applied_to_the_single_attempt`,
   que verifica la intenció supervivent). Remapejats només IDs a `impl_*.md` (zero
   codi): `--all` torna a PASS. El `requirements.md` de `timeout_scaling` R2 encara
   cita el ladder vell (2048/4096/8192) — staleness documentada, fora d'abast.
4. **Evicció de `smoke-r5.md`:** primer a `harness/logs/` (ignorat per git) i mogut a
   `harness/specs/discriminative_tasks/` perquè el test R5 el necessita en un checkout
   net. El `.log` complet resta sense versionar (gitignore `*.log`).

## Veredicte

**APPROVED** — demano el Completion Gate humà per a `discriminative_tasks`. Després del
Gate: `remeasure_pool` → `in_progress` i re-mesura completa (10 llama + Strata).
