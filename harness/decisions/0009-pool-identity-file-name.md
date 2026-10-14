# ADR-0009: Pool identity is the model file name, never the path it was measured with

- **Date:** 2026-10-14
- **Status:** accepted
- **Feature:** project-level

## Context

The pool is keyed per `(model, thinking)`, and the key was `config.slug(model)` — a
pure string transform that keeps whatever path arrived. It arrives in two shapes:
`--models` resolves through `config.MODELS_DIR.glob(...)`, which yields **absolute**
paths, while a hand-passed string that already exists as a file (`models/x.gguf` from
the workspace root) is used **as is** and stays relative.

Measured consequence (2026-10-13): qwen36 sat in the pool twice — 11:32 relative,
19:28 absolute — so the scoreboard listed the same model twice, one of them as
`_home_jordi_ia_llama_models_qwen36-…`, the compare picker offered it twice, and every
consumer that groups the pool by model (C8 optimal-mode pairing, compare ranks,
`--forget` by bare name) treated the two rows as two different models. The harness's
own question — "is this the same model?" — must not depend on how the caller typed the
path.

## Decision

A model is identified by its **file name**, not by the path it was measured with:

- `run.model_id()` stores a path relative to the workspace for llama; an absolute path
  outside the workspace is kept as given (models can live on another disk, and there the
  path *is* the identity).
- `report._key_of()` normalises with `_model_stem` before slugifying, so a legacy row
  inherited with an absolute path collapses with its relative twin — `load_pool()` keeps
  the most recent one, chronologically, as it already did for duplicates.
- Strata is untouched: the config stem (`strata-iq3_xxs`) is already the full identity
  (model + quant + configuration).

## Alternatives considered

- **Strip the noise at display time** (`_display_slug` learning to hide `_home_...`
  prefixes) — rejected: it fixes the looks and leaves one model with two rows, forcing
  every consumer to compensate for a defect the data should not have.
- **Force absolute paths everywhere** — rejected: the pool becomes machine-specific and
  unreadable; `results/report.html` is published to gh-pages, and the CLI prints the
  slug.
- **Reject absolute paths at the CLI** — rejected: it turns a legitimate invocation
  (`--models /abs/path/model.gguf`) into an error instead of understanding it.

## Consequences

- The `(model, thinking)` uniqueness invariant holds however `--models` was written:
  a re-run replaces the row instead of adding a twin.
- The legacy absolute row disappears on the next load (collapsed with the relative one)
  and is replaced by a clean row the next time that model runs.
- A row can always be matched against `models/<file name>.gguf` without normalising
  paths first; the invariant is covered by tests on both sides (`tests/test_run_cli.py`
  for the stored id, `tests/test_report.py` for the key and the twin collapse).
- Reversibility: cheap (two functions), but reverting would resurrect the defect on the
  first glob-driven run — the reason this is written down instead of left in a comment.
