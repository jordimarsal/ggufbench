# Design: timeout_scaling

## Files to create or modify

| Fitxer | Canvi |
|---|---|
| `graders.py` | nova `code_timeout(budget, gen_tps)`; `grade_code(..., gen_tps=None)` i cada intent de l'escala passa `timeout=code_timeout(budget, gen_tps)` al client |
| `run.py` | `_bench_one` passa `gen_tps` (el de la dimensió speed, ja mesurada abans) a `grade_code` |
| `harness/decisions/0001-code-timeout-token-budget.md` | ADR-0001 (R4) |
| `tests/test_graders.py`, `tests/test_config.py` | tests R1/R2/R5 + pesos intactes (ja hi eren) |

## Public signatures

```python
def code_timeout(budget: int, gen_tps: float | None) -> int:
    """clamp(90, 60 + (budget/gen_tps)*1.25, 600); 90 sense gen_tps."""

def grade_code(client_mod, tasks, max_turns=8, on_task=None, model_slug=None,
               gen_tps: float | None = None) -> dict: ...
```

## Exceptions and error cases

| Cas | Comportament | Req |
|---|---|---|
| Sense gen_tps (run sense dimensió speed) | 90 s fixes | R1 |
| gen_tps molt alt (model ràpid) | El sostre de 600 s i el pis de 90 s limiten sempre | R1 |
| Timeout malgrat l'escalat | Exclusió, com ara (R3) — registrada a la traça | R3 |

## Discarded alternatives

1. **Timeout pla de 300 s** — simple, però dóna a un model a 130 t/s 12 vegades més
   pressupost de tokens real que a un de 38 t/s: descartat.
2. **Desactivar el pensament a tots els models** (`enable_thinking=false`) — canviaria
   QUÈ es mesura (la capacitat del model tal com ve de fàbrica) i introduiria una
   asimetria amb el bench oficial d'Strata: descartat per ara; és una decisió de
   política separada (possible ADR futur).
3. **No fer res** — cobertura correlacionada amb velocitat al marcador publicable:
   descartat (és el biaix que aquesta feature elimina).
