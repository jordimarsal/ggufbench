# ADR-0001: The budget of a code task is in tokens; the clock is only an anti-hang guard

- **Date:** 2026-10-09
- **Status:** accepted
- **Feature:** timeout_scaling

## Context

With the fixed 60 s per-request timeout, models generating at 38-44 t/s that **think**
(Qwen3.8 with `--jinja`: thinking on by default) run out of coverage on long code
tasks — especially hard ones: the timeout expires while the model is still legally
producing tokens. In the 2026-10-09 re-measure, one model accumulated 20 such
exclusions mid-run. The exclusion does not lower the score, but it removes coverage:
the publishable sample ends up biased toward fast models, and the loss correlates
with speed — exactly the silent bias a benchmark cannot afford.

## Decision

The real budget of a code task is the **token** one (`CODE_LADDER`, same for
everyone). Each attempt's timeout derives from the model's **measured** speed:
`code_timeout(budget, gen_tps) = clamp(90, 60 + (budget/gen_tps)*1.25, 600)`
seconds, and a fixed 90 s when there is no measured speed. A timeout (now as before)
is an **exclusion**, never a fail.

## Alternatives considered

- **Generous flat timeout (300 s)** — simple, but a model at 130 t/s gets 12 times the
  real token budget of one at 38 t/s: same injustice, better hidden.
- **Disabling thinking on all models** (`enable_thinking=false`) — would change
  WHAT is measured (the model as it comes from the factory) and remove information; stays as
  a possible future policy decision, not a timeout patch.
- **Do nothing** — the publishable scoreboard keeps coverage correlated with
  speed: explicitly discarded.

## Consequences

- Slow models now take longer to measure (that is how they sell themselves): the full
  re-measure may stretch. The **speed** dimension (0.15) remains the only one scoring speed.
- The formula lives in `graders.code_timeout` and is tested (floor 90 s, ceiling 600 s,
  fallback without `gen_tps`): cheap to revert if a better criterion appears.
- Any future budget change (`CODE_LADDER`) automatically drags the timeout — one less
  thing to remember.
- Reversibility: cheap (a pure function + a parameter).
