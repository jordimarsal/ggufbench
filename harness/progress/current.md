# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** discriminative_tasks (id 5, in_progress) — i després remeasure_pool (id 2, blocked → in_progress)
- **Started:** 2026-10-10
- **Agent:** hybrid (un agent, rols sequencials)

## Plan

- Implementar `discriminative_tasks` per batches T1-T10 (spec aprovada al Spec Gate 2026-10-10).
- Un cop T8 (estructural) verd: desbloquejar `remeasure_pool` i executar la re-mesura completa (llama batch → Strata) — d'aquesta run en surt l'evidència del fum de discriminació (R5).
- T10: docs (SPEC, AGENTS.md), traçabilitat, review.md → demanar Completion Gate de feature 5; després tancar remeasure_pool (T2-T5).

## Log

- T1-T3 (batch-1.log): loader `_expert` → level; `--level easy|hard|expert`; `EXTRA_FILES` als 4 runners (java compila tots els `.java`) + validació de noms plans al loader; `tasks_version = "v3"`; by_level/report amb expert.
- T4 (batch-2.log): tasques expert python — `vault_engine_expert` (mòdul), `metrics_debug_expert` (debug 3 errors), `readings_etl_expert` (dades + `readings.csv`). Fix test: `3 × 2.25 = 6.75` (revenue 96.65); apòstrof trencat al TEST_CODE de vault.
- T5 (batch-3.log): tasques expert bash — `num_report_expert`, `log_filter_debug_expert`, `access_agg_expert`. Aprenentatge: `LC_NUMERIC=ca_ES.UTF-8` → coma decimal; el prompt exigeix punt i el ref força `LC_ALL=C`.
- T6 (batch-4.log): tasques expert java — `interval_codec_expert`, `ledger_debug_expert` (3 errors aïllats amb instància per error al test), `csv_index_expert`.
- T7 (batch-5.log): tasques expert typescript — `proc_registry_expert`, `event_debug_expert`, `jsonl_agg_expert`. Fix test: stats s'ha de fer amb `max=3` abans de retallar.
- T8 (batch-6.log): `tests/test_expert_tasks.py` (>=3 per llengua, fixtures, context enganxat).
- Validació d'autor de les 12: ref=OK i partial=falla al tercer comportament a `harness/logs/discriminative_tasks/author-validation.log` (solucions a /tmp, NO es commiten).
- Registre a `feature_list.json`: la comanda del checkpoint anterior havia caigut — feature 5 afegida (in_progress) i `remeasure_pool` → `blocked` (coherent amb blocked.md). `validate-feature-list.py` OK.
- Provisori: `feature_list.json` + specs + tasques encara sense commit.
- **T9 (fum R5):** llançat amb `--dims code --level expert` sobre 2 models (27B fort vs
  8B feble) → `harness/logs/discriminative_tasks/smoke-r5.log`. Motiu: el validator
  prohibeix 2 features `in_progress` a la vegada, així que la re-mesura completa queda
  per a remeasure_pool un cop discriminative_tasks tanqui el Completion Gate (el
  `blocked.md` ja ho documenta); el fum R5 (≥2 models) és el que necessita la feature 5.
  **Intent 1 (`--dims code`) va fallar**: sense `speed` no hi ha `gen_tps` →
  `code_timeout` = 90 s fixes → les tasques expert timeouteen
  (`smoke-r5-attempt1.log`; defecte D6 de MILLORA, afegit avui). Intent 2 amb
  `--dims speed,code` (mateixa cadena `gen_tps` que la re-mesura real).
  Nota: el pkill de l'intent 1 va deixar un `llama-server` orfe (kill abrupte → el
  `finally: sm.stop()` no va netejar) — matat a mà; en matar una run, verificar que el
  servidor cau.
  Després del fum: restaurar `pool.jsonl` des de `pool.pre-remeasure.jsonl` per no
  deixar el pool barrejat (condicions homogènies documentades a blocked.md).
- **T10 (docs, feta):** SPEC.md CLI `--level easy|hard|expert`; `tasks_version` documentat
  com a etiqueta v1/v2/v3 (abans deia "hash"); `by_level` al example JSON de code;
  AGENTS.md regla 3 ampliada (nivell expert, EXTRA_FILES, v3).
- Pròxim: acabar T9 (extreure gap ≥20 pts del fum → test mecànic + tick), `impl_discriminative_tasks.md`
  (R1-R6 fets, R5 = test sobre el log del fum, R7 = retired), check-traceability → review.md,
  batch-7.log + tick T10 → demanar Completion Gate.
- **Fet després (sessió 10-oct, "continua"):** test R7 `test_r7_retired_no_efficiency_dimension`
  (test_config.py, verd); `impl_discriminative_tasks.md` escrit (R1-R4/R6/R7 done, R5 pending);
  `check-traceability --feature discriminative_tasks` → **7/7 PASS**; `tests/test_smoke_evidence.py`
  + `/tmp/opencode/extract_r5.py` (log → `smoke-r5.md` versionable) llestos i provats amb mostra
  sintètica. Fum intent 2 en curs (27B: 1/12 ✓ log_filter_debug, 3× `no code block`).
  **Pendent del fum:** generar `smoke-r5.md`, verificar gap, tick T9, `init.sh` → batch-7.log,
  tick T10, review.md + verdict, commit (`docs`+`tests`) i **Completion Gate**.

## Next step

1. Commit de la implementació (Conventional Commits).
2. Desbloquejar `remeasure_pool` (status → in_progress, anotar blocked.md) i llançar la re-mesura:
   llama batch (`/tmp/opencode/llama_batch.txt` → `harness/logs/remeasure_pool/batch-llama.log`),
   després Strata `iq3_xxs` quan el batch llama hagi parat completament. Mai tots dos alhora.
3. Amb les dades de la run: evidència R5 (>=2 models, >=1 tasca expert amb >=20 punts de gap), T10
   (docs + `impl_discriminative_tasks.md` + check-traceability → review.md) → Completion Gate de
   discriminative_tasks; després remeasure_pool T2-T5 (pool v3 + `by_level`, report sense banner, gate).
