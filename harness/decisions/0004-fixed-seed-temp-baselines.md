# ADR-0004: Identical sampling for every model — temp 0.2 / seed 42, pinned at two levels

- **Date:** 2026-10-12
- **Status:** accepted
- **Feature:** project-level

## Context

The scoreboard compares models, not sampler configurations: "which GGUF for
opencode" only has an answer if observed differences come from the weights.
SPEC §2 ("same conditions") fixes the common baseline in
`config.SERVER_FLAGS`: `--temp 0.2`, `--top-p 0.95`, `--seed 42`,
`--repeat-penalty 1.1`, `--repeat-last-n 256` (plus `--parallel 1`,
`--jinja`, KV `q4_0/q4_0`). Sampling is a base flag, so AGENTS.md rule 2
applies: no change without a pool re-measure. Per-request determinism also
underwrites ADR-0002 — with fixed seed/temp, a larger `max_tokens` reproduces
the same generation as a smaller one (deterministic prefix).

## Decision

Every model is measured with identical sampling, pinned at two levels so
server-side drift cannot leak in: the server baseline (`config.SERVER_FLAGS`,
constants `TEMPERATURE = 0.2`, `SEED = 42`) and the request body —
`client.chat` sends `temperature` and `seed` on every call "to guarantee
repeatability even if the server changes configuration". Model profiles
(`models/*.txt`) compete on model flags only; none overrides a sampling flag,
and any that did would trigger the rule-2 re-measure with the applied flags
recorded in `model_config_flags`.

## Alternatives considered

- **Per-model tuned sampling** (temp/seed picked for each model's best score)
  — rejected: breaks comparability outright; it measures the tuning effort,
  not the model, and opens the door to cherry-picking.
- **Sampling as a free `.txt` parameter** like `--spec-type`/`-md` — rejected:
  MTP flags are a legitimate competition axis (recorded, stack-level); sampling
  changes what the metric *means*, which is a different category entirely.
- **Higher temp "to surface real capability"** — rejected: temp 0.2 + seed 42
  is the reproducibility trade; n=1 noise is accepted and documented (SPEC §2).

## Consequences

- Deterministic-ish repeats: same prompt + same seed → same generation
  prefix; reruns and ladder-free budgets stay provably comparable.
- No per-model cherry-picking: the sampler is not an available degree of
  freedom for a profile.
- n=1 noise is accepted and documented (SPEC §2 sampling note): the scoreboard
  is a ranking on this harness, close rows (±0.01 global) are ties in
  practice; `--runs N` (mean ± spread) is the planned fix, not a sampler
  change.
- Reversibility: cheap — the constants live in `config.py`; changing any of
  them deliberately triggers the AGENTS.md rule-2 pool re-measure, by design.
