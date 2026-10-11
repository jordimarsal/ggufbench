# Design: timeout_scaling

## Files to create or modify

| File | Change |
|---|---|
| `graders.py` | new `code_timeout(budget, gen_tps)`; `grade_code(..., gen_tps=None)` and every attempt of the ladder passes `timeout=code_timeout(budget, gen_tps)` to the client |
| `run.py` | `_bench_one` passes `gen_tps` (the speed dimension's, already measured before) to `grade_code` |
| `harness/decisions/0001-code-timeout-token-budget.md` | ADR-0001 (R4) |
| `tests/test_graders.py`, `tests/test_config.py` | tests R1/R2/R5 + weights intact (already there) |

## Public signatures

```python
def code_timeout(budget: int, gen_tps: float | None) -> int:
    """clamp(90, 60 + (budget/gen_tps)*1.25, 600); 90 without gen_tps."""

def grade_code(client_mod, tasks, max_turns=8, on_task=None, model_slug=None,
               gen_tps: float | None = None) -> dict: ...
```

## Exceptions and error cases

| Case | Behavior | Req |
|---|---|---|
| Without gen_tps (run without the speed dimension) | fixed 90 s | R1 |
| Very high gen_tps (fast model) | The 600 s ceiling and the 90 s floor always bound it | R1 |
| Timeout despite scaling | Exclusion, as now (R3) — recorded in the trace | R3 |

## Discarded alternatives

1. **Flat 300 s timeout** — simple, but it gives a model at 130 t/s 12 times the real
   token budget of one at 38 t/s: discarded.
2. **Disabling thinking on all models** (`enable_thinking=false`) — would change
   WHAT is measured (the model's out-of-the-factory capability) and introduce an
   asymmetry with Strata's official bench: discarded for now; it is a separate
   policy decision (possible future ADR).
3. **Do nothing** — coverage correlated with speed in the publishable scoreboard:
   discarded (it is the bias this feature removes).
