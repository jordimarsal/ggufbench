# ADR-0005: A second serving engine — Strata is measured, not assumed

- **Date:** 2026-10-12
- **Status:** accepted
- **Feature:** project-level

## Context

The question "which GGUF for agentic work" includes the serving stack, not
just the weights: the same quant family performs differently under a different
runner. Strata (`config.py`) is that second stack: GSQ-quantized packs
(`Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-*.gguf`), its own expert/conversation
cache (`--expert-cache auto`), MTP speculative decoding (`--mtp`, `--spec 4`)
and `--max-context 131072` — iq3_xxs at 131k ctx. llama-server stays as the
baseline everyone can reproduce. If Strata were not measured, its stack-level
wins would be folklore; if it were measured loosely, the scoreboard would mix
receipt-less claims.

## Decision

`--engine strata` is a first-class engine: `server.ENGINES = ("llama",
"strata")`; `run.py` resolves `--models iq3_xxs` →
`Strata/strata-iq3_xxs.json` (one config per model: pack, context, GPUs, MTP),
started via `strata_command()` as `<Strata/.venv>/bin/python serve/server.py
--engine strata --config <json> --port 8080` (`config.STRATA_PORT`; the
harness' own python is only a fallback that fails loudly — the engine needs
jinja2/numpy). It speaks the same OpenAI contract and emits llama.cpp-named
`timings`, so the 4 dimensions work unchanged. Results carry `engine` +
`server_build` (`Strata/engine/BUILD.json`, e.g. 0.1.42); the pool identity is
the config root (`strata-iq3_xxs`).

## Alternatives considered

- **llama.cpp only** — rejected: misses stack-level wins like Strata's iq3_xxs
  at 131k ctx with cache + MTP; the comparison would answer a narrower
  question than the one that matters for opencode.
- **More engines (vLLM, ...)** — rejected: each engine needs receipts parity
  (engine + server_build in every result, configs in git, readiness semantics —
  Strata waits for `/health` `loaded`, `STRATA_READY_TIMEOUT = 600` s for the
  34-43 GB load); maintenance grows linearly, insight does not.
- **Wrap Strata behind a llama-server emulation layer** — rejected: dishonest
  receipts; the engine is precisely the thing being measured.

## Consequences

- Golden rule (AGENTS.md rule 1): **never llama-server and Strata at the same
  time** — both own the same 2× RTX 5080 (`strata-iq3_xxs.json` declares
  `gpu: [0, 1]`). `ServerManager` owns the full lifecycle
  (`start_new_session` + `killpg`: without it the `engine/strata` child
  outlives the parent and keeps holding VRAM).
- Every harness feature must work on both engines (thinking body, dims, pool
  upsert): the "same contract" is an obligation per feature, not a hope.
- Strata starts in 1-3 min (tens of GB into RAM): runs are slower to boot;
  `READY_TIMEOUT` is per-engine (240 s llama / 600 s strata).
- Reversibility: cheap — dropping the engine is deleting the strata branch in
  `ENGINES`/`run.py`; llama rows stand alone.
