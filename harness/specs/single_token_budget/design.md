# Design: single_token_budget

## Files to create or modify

| Fitxer | Canvi |
|---|---|
| `graders.py` | `CODE_MAX_TOKENS = 16384` (sostre de context), `CODE_LADDER = [CODE_MAX_TOKENS]`; tracca amb `out_tokens` |
| `harness/decisions/0002-single-code-token-budget.md` | ADR-0002 |
| `tests/test_graders.py` | TestCodeEscalation -> TestCodeBudget (4 tests) |
| `AGENTS.md` | Actualitzar la nota de calibracio (bloc harness:project / notes) |

## Public signatures

(cap canvi public: `CODE_LADDER`/`CODE_MAX_TOKENS` constants; la tracca guanya `out_tokens`)

## Exceptions and error cases

| Cas | Comportament | Req |
|---|---|---|
| Bucle degenerat sense EOS | Sostre de tokens 8192 + guarda de rellotge 600 s (ADR-0001) -> exclusio | R1 |
| Model concise | Para a l'EOS molt abans del sostre: cost zero | R1 |
| Pressupost guardat antic (< 8192) | S'honora: per construccio, el guardat es el que va funcionar | R3 |

## Discarded alternatives

1. **Mantenir l'escala** — 1-2 peticions mortes per tasca amb models que pensen.
2. **Comencar a 4096** — mateixa objeccio.
3. **16384** — bucles degenerats de 7+ min a 38 t/s: excessiu per aquesta classe de
   models i tasques (el guarda de 600 s ja limita).
