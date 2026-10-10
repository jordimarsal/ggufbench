# Implementació: remeasure_pool

feature: remeasure_pool

**Sessió:** 2026-10-10 (hybrid — un agent, rols sequencials)
**Spec Gate:** aprovat (2026-10-09) → blocked → in_progress (desbloqueig 2026-10-10)

## Desviacions de l'spec aprovat (declarades per al Gate)

L'spec es va aprovar abans de les decisions `thinking_batches` i diu v2/hard/una fila
per model/`--models all`. La realitat executada, aprovada pel revisor humà en decisions
posteriors documentades (`blocked.md`, gates de features 5 i 6), és:

- **R1 (v2/hard → v3/hard+expert):** el task set vigent quan es mesura inclou el nivell
  expert; mesurar amb v2 hauria estat mesurar condicions ja superades. Superat per
  decisió humana (Completion Gate de `discriminative_tasks`).
- **R1/R3 (una fila per model → dues, una per mode):** el doble batch think/no-think
  (decisió humana + Spec/Completion Gates de `thinking_batches`) exigeix clau
  `(slug, thinking)`. "Cap entrada d'una condició anterior" se satisfà: les 11 legacy
  v1 s'arxivaren al backup i el pool final en té 22 de fresques (11 off + 11 on).
- **T2 (`--models all` → llista explícita de 10):** `all` globejaria models fora del
  pool (el directori en té més); la llista explícita garanteix R1 ("every model
  present in the pool"). Comportament equivalent, més estricte.

## Batches (evidències a harness/logs/remeasure_pool/)

| Batch | Contingut | Log |
|---|---|---|
| T1 | Pre-flight: sense servidors, ports lliures, suite 187 passed, pool homogeni v1, config Strata, `-c 65536` als 3 perfils, sonda HTTP 200 del kwarg contra llama-server | preflight.log |
| T2 | llama OFF (10 models, dims/levels complets, exit 0, ~31 min) + llama ON (10/10 amb restart documentat per mort prematura del procés a 3/10) | batch-llama-off.log, batch-llama-on.log |
| T3 | Strata OFF (code 0.95) + Strata ON (code 0.92, HIGH no trenca dims petites), verificat cap motor orfe entre batchs | batch-strata-off.log, batch-strata-on.log |
| T4 | Pool 22 fresques (una data, v3, by_level amb expert, exclosos registrats) + `results/report.html` sense banner, badges 11+11 | summary.log (scoreboard) |
| T5 | Aquest fitxer + traçabilitat + review + gate | summary.log (comprovacions) |

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_upsert_keeps_both_thinking_modes test_thinking_on_off_passthrough test_table1_labels_think_and_excluded | batch-llama-off.log batch-llama-on.log batch-strata-off.log batch-strata-on.log (10+10+1+1 ✓, exit 0) | done |
| R2 | test_ports_and_ready_timeout_per_engine | pre-launch checks (cap motor viu abans de cada batch, current.md); logs seqüencials, mai solapats | done |
| R3 | test_legacy_row_without_thinking_coexists_with_off test_upsert_keeps_both_thinking_modes | pool.jsonl: 22 files (11 off + 11 on), totes v3 d'una data; legacy al backup pre-remeasure | done |
| R4 | test_banner_only_with_mixed_dates test_think_badges_and_excluded_line | results/report.html regenerat: sense banner, badges 11+11 | done |
| R5 | test_runs_filenames_distinguish_mode | harness/logs/remeasure_pool/ (6 logs) + summary.log | done |

Nota de traçabilitat: R1-R3 es verifiquen per **evidència de run** (logs + inspecció
del pool a summary.log), no per test unitari — el pool és gitignored i cap test pot
dependre'n en un checkout net. Els IDs citats són la capacitat mecànica que ho fa
possible (clau dual, flag, render), tots existents i verds.
