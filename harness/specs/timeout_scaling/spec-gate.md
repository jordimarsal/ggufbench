# Spec Gate — timeout_scaling

**Date:** 2026-10-09 · **Decision:** APPROVED (pending → spec_ready)

Reviewer: Jordi (human gate). The approval includes the exact formula chosen
explicitly by the reviewer mid-execution of remeasure_pool:
`clamp(90, 60 + (budget/gen_tps)*1.25, 600)`, keeping exclusions as the
semantics, plus ADR-0001. Approved procedure: stop the in-flight re-measure,
implement, and repeat the whole re-measure under the new protocol.
