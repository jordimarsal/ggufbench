# Tasks: thinking_batches

- [x] T1: CLI `--thinking on|off` (default off) + body kwarg + `thinking` in the result;
      prompts/dims do not change with the mode (identical on/off bodies test)
      depends_on: (none)
      refs: R1, R6

- [x] T2: Pool key `(slug, thinking)` (save/load/forget + runs filenames) +
      legacy-tolerant render (`—` mark); `slug` intact
      depends_on: T1
      refs: R2

- [x] T3: `token_budget` keyed by `(model, thinking)` + `_schema = 2` (16384 era
      ignored and regenerated)
      depends_on: T2
      refs: R2

- [x] T4: `CODE_MAX_TOKENS = 32768` + clock cap 1000 (same formula);
      update BODY (not names) of the affected timeout_scaling tests
      depends_on: T3
      refs: R3

- [x] T5: Report: `THINK` column + ` (N excl.)` in Table 1, mode mark in Table 3,
      banner intact (existing banner test green)
      depends_on: T2
      refs: R4, R5

- [x] T6: HTML: mode badge + `excluded: N/M` line on the card; matrix intact
      depends_on: T5
      refs: R4, R5

- [x] T7: Docs (SPEC: `--thinking`, 32768 budget, THINK column; AGENTS.md;
      MILLORA: close D6 as superseded by this feature) + traceability +
      harness/init.sh + request Completion Gate
      depends_on: T4, T6
      refs: R1, R2, R3, R4, R5, R6, R7
