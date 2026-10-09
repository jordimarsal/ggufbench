# Implementacio: single_token_budget

feature: single_token_budget

**Sessio:** 2026-10-09 (hybrid)

## Traceability

| Requirement | Test(s) | Implementation file(s) | Status |
|-------------|---------|------------------------|--------|
| R1 | test_single_generous_budget_resolves_long_output | graders.py CODE_LADDER CODE_MAX_TOKENS | done |
| R2 | test_output_tokens_recorded_in_trace | graders.py grade_code | done |
| R3 | test_stored_budget_still_honoured | graders.py grade_code token_budget.py | done |
| R4 | test_no_save_when_default_suffices test_single_generous_budget_resolves_long_output | tests/test_graders.py | done |
