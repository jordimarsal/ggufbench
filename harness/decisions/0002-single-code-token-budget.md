# ADR-0002: A single generous token budget for code tasks (end of the ladder)

- **Date:** 2026-10-09
- **Status:** accepted
- **Feature:** single_token_budget (reviewer proposal mid re-measure)

## Context

The ladder `CODE_LADDER = [2048, 4096, 8192]` was born to measure models without a
thinking chain: if the block did not fit in 2048 tokens, it escalated. With models that **think**
(Qwen3.8, factory thinking with `--jinja`), the first attempt often spends 1000-2000
tokens just reasoning: the ladder becomes 1-2 wasted requests per
task (the final result is identical, but paid three times in wall-clock).

## Decision

A single budget for all code tasks: `CODE_MAX_TOKENS = 16384`,
`CODE_LADDER = [16384]` — the harness context ceiling (`CONTEXT_FIXED` minus
prompt), which is the reviewer-proposed `2×8192` absorbed as a single budget. Key
technical point: with fixed seed/temp, `max_tokens` is a **ceiling, not a target** — an
attempt at 16384 reproduces the same generation as any lower ladder (deterministic
prefix), so the score is provably identical and only dead time is removed. Efficiency
(output tokens per task) is recorded in the trace
(`out_tokens`) as an informative metric, never as a penalty.

## Alternatives considered

- **Keep the original ladder [2048, 4096, 8192]** — 1-2 dead requests per task
  with thinking models: discarded for pure overhead.
- **Ladder [8192, 16384]** — same result as the single 16384 (deterministic prefix) but
  reintroduces the ladder and degenerate loops cost 2 attempts (329+598 s) instead
  of one (598 s, within the ADR-0001 guard): discarded.
- **Single 8192 (first version of this ADR)** — left the long thinking queue
  (8-16k tokens) of thinking models unmeasured: discarded by the reviewer.

## Consequences

- Fewer requests and less time per run with thinking models; concise models do
  not change (they stop at EOS anyway).
- `token_budgets.json` loses half its meaning (the "calibrated budget" will always be
  8192 or unreachable): the mechanism is kept for compatibility and in case a
  laddered budget returns.
- Verbosity stops being a hard ceiling and becomes a metric: if scoring it were ever
  wanted, it would be an explicit new dimension, not a timeout side effect.
- Reversibility: cheap (one constant + one test).
