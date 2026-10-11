# Spec Gate — hard_code_tier

**Date:** 2026-10-09
**Decision:** APPROVED (pending → spec_ready → in_progress)

- Reviewer: Jordi (human gate, via session assistant).
- Reviewed input: `requirements.md` (R1-R8) + `design.md` (files, signatures,
  error cases, 5 discarded alternatives) + `tasks.md` (12 tasks, 6 batches).
- Decisions taken by the reviewer before the spec:
  - 4 hard tasks per language (16 total) in the first iteration.
  - Score folded inside code (same dimension and weights), by_level breakdown in
    the report.
- Output: batch-by-batch implementation with evidence in `harness/logs/hard_code_tier/`.
  Completion Gate will require full R1-R8 traceability + green `harness/init.sh`.
