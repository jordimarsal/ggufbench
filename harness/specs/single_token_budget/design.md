# Design: single_token_budget

## Files to create or modify

| File | Change |
|---|---|
| `graders.py` | `CODE_MAX_TOKENS = 16384` (context ceiling), `CODE_LADDER = [CODE_MAX_TOKENS]`; trace gains `out_tokens` |
| `harness/decisions/0002-single-code-token-budget.md` | ADR-0002 |
| `tests/test_graders.py` | TestCodeEscalation -> TestCodeBudget (4 tests) |
| `AGENTS.md` | Update the calibration note (harness:project block / notes) |

## Public signatures

(no public change: `CODE_LADDER`/`CODE_MAX_TOKENS` constants; the trace gains `out_tokens`)

## Exceptions and error cases

| Case | Behavior | Req |
|---|---|---|
| Degenerate loop without EOS | 8192 token ceiling + 600 s clock guard (ADR-0001) -> exclusion | R1 |
| Concise model | Stops at EOS well before the ceiling: zero cost | R1 |
| Old stored budget (< 8192) | Honoured: by construction, the stored one is what worked | R3 |

## Discarded alternatives

1. **Keep the ladder** — 1-2 dead requests per task with thinking models.
2. **Start at 4096** — same objection.
3. **16384** — degenerate loops of 7+ min at 38 t/s: excessive for this class of
   models and tasks (the 600 s guard already bounds it).
