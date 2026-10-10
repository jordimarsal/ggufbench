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

## Next step

1. Commit de la implementació (Conventional Commits).
2. Desbloquejar `remeasure_pool` (status → in_progress, anotar blocked.md) i llançar la re-mesura:
   llama batch (`/tmp/opencode/llama_batch.txt` → `harness/logs/remeasure_pool/batch-llama.log`),
   després Strata `iq3_xxs` quan el batch llama hagi parat completament. Mai tots dos alhora.
3. Amb les dades de la run: evidència R5 (>=2 models, >=1 tasca expert amb >=20 punts de gap), T10
   (docs + `impl_discriminative_tasks.md` + check-traceability → review.md) → Completion Gate de
   discriminative_tasks; després remeasure_pool T2-T5 (pool v3 + `by_level`, report sense banner, gate).
