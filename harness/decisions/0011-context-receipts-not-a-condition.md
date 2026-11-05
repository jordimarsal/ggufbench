# ADR-0011: Context receipts are recorded metadata, never a pool condition

- **Date:** 2026-11-05
- **Status:** accepted
- **Feature:** context_receipts

## Context

A dev.to reader (2026-11) asked how much context a local model burns to pass
the same tasks: the agent loop re-sends the whole conversation every turn, so
two models with the same pass rate can cost very differently in sent tokens.
The trace already recorded `out_tokens` and the timings, but `prompt_tokens`
(tokens SENT per call) was counted nowhere. Recording it creates a new number
in every result — and every new number in this pool raises the same question
`thinking_batches` (ADR-0006) and `lora_eval` answered with a key extension:
does it split the pool?

## Decision

Receipts are **recorded metadata of the same measurement, not a condition**:
the pool key stays `(slug, thinking, lora)`, `task_signature` is untouched,
nothing is invalidated and no re-measure is required. Rows measured before the
field simply lack it, and every renderer prints '?' for them (the same
tolerance as unmeasured dimensions). The number travels inside the existing
per-run receipt files and pool rows; it is informational and never enters
scores, weights or fold rules.

## Alternatives considered

- **Pool key extension** (`(slug, thinking, lora, receipts)`) — rejected: the
  presence of a measurement cannot be a measurement condition; it would split
  identical-condition rows, break the mixed-conditions banner logic and force
  a pointless pool re-measure.
- **Score integration** (a fifth scored axis "context cost") — rejected by the
  feature's own no-goals: the four weights are frozen until the next full
  re-measure, and tokens/session is hardware- and harness-dependent in ways
  the score's comparability rules do not cover yet.

## Consequences

- Old and new rows coexist in one pool; the renderers own the '?' duty.
- `report.receipts()` is the single read seam — board and HTML never reach
  into the dim dicts themselves.
- Cheap to reverse: drop the columns and the rollup keys, nothing else
  references them.
- If a future feature wants to SCORE context cost, that is a new ADR with a
  re-measure, not an edit of this one.
