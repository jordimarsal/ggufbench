# Review — feature 2 (remeasure_pool)

**Verdict:** APPROVED (pendent del Completion Gate humà)

Revisor: mateix agent en mode review (hybrid). Aquesta feature no canvia codi (només
execució + evidència): la revisió verifica requisits, estat del pool i logs.

## Requirement traceability ↔ tests

- R1: [x] Evidència: 4 logs amb 10+10+1+1 models ✓, exit 0 (excepte restart
  documentat); pool amb 22 files v3. Tests capacitat: `test_upsert_keeps_both_thinking_modes`,
  `test_thinking_on_off_passthrough`, `test_table1_labels_think_and_excluded`.
  Desviació declarada: v3+expert en comptes de v2+hard (condicions vigents al mesurar).
- R2: [x] Evidència: checks pre-batch (cap motor viu) + logs seqüencials sense
  solapament + 0 orfes al final. Test afí: `test_ports_and_ready_timeout_per_engine`.
- R3: [x] Evidència: pool 22 files (11 off + 11 on), una data, cap legacy (al backup).
  Desviació declarada: dues files per model (una per mode), no una.
  Tests: `test_legacy_row_without_thinking_coexists_with_off`,
  `test_upsert_keeps_both_thinking_modes`.
- R4: [x] Evidència: `results/report.html` regenerat, grep "Condicions barrejades" = 0,
  badges 11+11. Tests: `test_banner_only_with_mixed_dates`,
  `test_think_badges_and_excluded_line`.
- R5: [x] Evidència: 6 logs + summary.log (scoreboard + comprovacions).
  Test: `test_runs_filenames_distinguish_mode`.

## Task completion

- T1–T4: [x]. T5: [x] amb aquest review (traçabilitat 5/5 + `--all` PASS + init verd).

## Checkpoints

- C1: [x] init.sh exit 0 (batch-verify.log: 187 passed, 1 skipped).
- C2: [x] en tancar: una sola `in_progress` → passarà a `done`; current.md actiu.
- C3: [x] cap canvi de codi en aquesta feature (verificat: `git status` només mostra
  specs/progress/docs; pool+logs+report.html ignorats; perfils `.txt` fora del repo).
- C4: [x] suite verda; cap test nou necessari (feature d'execució).
- C5: [ ] obert — tancament pendent del Gate.
- C6: [x] spec amb EARS; desviacions de l'spec documentades a l'impl (no reescrit
  l'aprovat); cada R<n> amb evidència + test afí.
- C7: [x] `audit_level: basic` — sense codi nou no hi ha superfície nova: (1) cap
  secret als logs commitejats (sortides de models, traces i scores); (2-4) executors/
  sandbox intactes; (5) report regenerat amb `_esc` intacte (test d'escapament verd);
  (6-7) servidors/xarxa intactes.

## Dades per al Gate humà (lectura ràpida)

- OFF mana en GLOBAL (MoE 0.95, gemma 0.89); ON clusteritza 0.71–0.83 arrossegat per
  latència del think (fins a 1707 ms) — la comparació vàlida és intra-mode.
- Code ON vs OFF: 27B forts pugen pensant (0.82→0.96, 0.87→0.95); MoE petit baixa
  (5 excloses); 8B idèntic (0.73/0.73 — no pensa ni lliure).
- Strata: OFF 0.95 → ON 0.92 en code; HIGH no trenca dims petites (tools 1.00).
- Expert mossega: code plegat OFF 0.73–0.88 (abans 0.84–1.00 en v1).

## Veredicte

**APPROVED** — demano el Completion Gate humà per a `remeasure_pool`.
