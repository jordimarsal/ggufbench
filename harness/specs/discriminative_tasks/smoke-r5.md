# Evidència R5 — fum de discriminació (discriminative_tasks)

Data: 2026-10-10 · `python3 -m benchmark.run --dims speed,code --level expert` sobre 2 models.

Log complet (`.log`, no versionat pel gitignore global): `smoke-r5.log`.
Símbols: `✓` passa · `✗` falla (inclou `no code block`: el model no lliura codi) · `⊥` error de servidor (soroll d'entorn, no compta com a discriminació).

| Tasca expert | models_qwen3_8-27b-ud-q5_k_m | models_qwen3-vl-8b-instruct-1m-q6_k | gap |
|---|---|---|---|
| access_agg_expert | ✗ | ✗ | 0 |
| csv_index_expert | ✗ | ✗ | 0 |
| event_debug_expert | ✓ | ✓ | 0 |
| interval_codec_expert | ✗ | ✗ | 0 |
| jsonl_agg_expert | ✗ | ✗ | 0 |
| ledger_debug_expert | ✗ | ✗ | 0 |
| log_filter_debug_expert | ✓ | ✗ | 100 |
| metrics_debug_expert | ✓ | ✓ | 0 |
| num_report_expert | ✗ | ✗ | 0 |
| proc_registry_expert | ✓ | ✗ | 100 |
| readings_etl_expert | ✗ | ✗ | 0 |
| vault_engine_expert | ✓ | ✓ | 0 |

Models: 2 · Tasques expert: 12 · Separen (✓ vs ✗): 2 · Gap màxim: 100 punts.

R5 es compleix si models >= 2, >= 1 tasca separen i gap max >= 20.
(Verificació mecànica: `tests/test_smoke_evidence.py`.)
