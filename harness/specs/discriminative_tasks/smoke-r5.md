SPEC GATE — discriminative_tasks

Approved: 2026-10-10 (Jordi, via session: "approved the new spec. continue")
Spec: requirements.md (R1-R6, R7 retired), design.md, tasks.md (T1-T10)
Relevant decisions: the _expert level reuses hard-level machinery;
EXTRA_FILES in the sandbox of the 4 runners (plain names validated at loader);
tasks_version -> v3; quality criterion = partial-solution resistance;
discrimination smoke (R5) inside the re-measure.
# Completion Gate — discriminative_tasks

**Date:** 2026-10-10 · **Decision:** APPROVED with changes (in_progress → done)

Gate checklist (docs/verification.md):

- [x] All tasks `[x]` in `tasks.md` (10/10), with batch logs in
  `harness/logs/discriminative_tasks/batch-{1..7}.log` + `author-validation.log` +
  `smoke-r5.log` / `smoke-r5-attempt1.log`.
- [x] Objective traceability: `check-traceability.py --feature discriminative_tasks`
  → 7/7 PASS (`traceability-check.txt`); `--all` → PASS.
- [x] Gates run first-hand: unittest suite (165 tests OK, 1 pre-existing skip) +
  `harness/init.sh` green (`batch-7.log`).
- [x] Author validation of the 12 expert tasks: ref OK, partial FAILS at the third
  behaviour (`author-validation.log`; solutions in /tmp, not committed).
- [x] R5 smoke with 2 real models: 2 expert tasks separate ✓/✗ with gap 100
  (`harness/specs/discriminative_tasks/smoke-r5.md`, mechanical test
  `tests/test_smoke_evidence.py`).
- [x] Own review (`review.md`): APPROVED verdict + basic security checklist
  confirmed + 4 observations (D6, token ceiling/think, ID remaps, restored pool).
- [x] Commits: `c982cb9` (expert tier) + `3fc5004` (docs) + `ef116f4` (harness).
- [x] Human approval recorded in `APPROVAL` (with the Q1 change: code budget
  starts at 32768, to implement in the next feature).

Flow closure: summary moved to `harness/progress/history.md`; next feature:
**thinking_batches** (new: dual think/no-think batch + 32768 budget + signalled
exclusions + pool key by `(slug, thinking)`) — the re-measure does not start until
its Completion Gate (`remeasure_pool` stays `blocked`).
# R5 evidence — discrimination smoke (discriminative_tasks)

Date: 2026-10-10 · `python3 -m ggufbench.run --dims speed,code --level expert` on 2 models.

Full log (`.log`, not versioned by the global gitignore): `smoke-r5.log`.
Symbols: `✓` passes · `✗` fails (includes `no code block`: the model delivers no code) · `⊥` server error (environment noise, does not count as discrimination).

| Expert task | models_qwen3_8-27b-ud-q5_k_m | models_qwen3-vl-8b-instruct-1m-q6_k | gap |
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

Models: 2 · Expert tasks: 12 · Separate (✓ vs ✗): 2 · Max gap: 100 points.
