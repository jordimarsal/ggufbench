# Implementation: timeout_scaling

feature: timeout_scaling

**Session:** 2026-10-09 (hybrid)

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_formula_floors_ceils_and_falls_back | graders.py code_timeout | done |
| R2 | test_scaled_timeout_applied_to_the_single_attempt | graders.py grade_code run.py | done |
| R3 | test_transient_timeout_still_excludes test_scaled_timeout_applied_to_the_single_attempt | graders.py | done |
| R5 | test_formula_floors_ceils_and_falls_back test_scaled_timeout_applied_to_the_single_attempt | tests/test_graders.py | done |

Note: R4 (ADR) retired in the spec — an ADR is not verified by test; the artifact lives in
harness/decisions/0001-code-timeout-token-budget.md and is reviewed in the review.
