# Implementacio: timeout_scaling

feature: timeout_scaling

**Sessio:** 2026-10-09 (hybrid)

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_formula_floors_ceils_and_falls_back | graders.py code_timeout | done |
| R2 | test_ladder_uses_scaled_timeouts | graders.py grade_code run.py | done |
| R3 | test_transient_timeout_still_excludes test_ladder_uses_scaled_timeouts | graders.py | done |
| R5 | test_formula_floors_ceils_and_falls_back test_ladder_uses_scaled_timeouts | tests/test_graders.py | done |

Nota: R4 (ADR) jubilada al spec — un ADR no es verifica per test; l'artefacte viu a
harness/decisions/0001-code-timeout-token-budget.md i es revisa a la review.
