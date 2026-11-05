# Tasks: context_receipts

- [ ] T1: `client.parse_usage(resp)` (usage.prompt_tokens → timings fallback → None)
      + tests (test_client.py pattern: hit, fallback, both absent)
      depends_on: (none)
      refs: R1

- [ ] T2: `grade_tools` / `grade_code` / `grade_speed` write `in_tokens` into every
      entry built from a response (omitted on transport-error entries), next to
      out_tokens/gen_tps + fake-client tests
      depends_on: T1
      refs: R2

- [ ] T3: `agent.run_agent` records per-turn `turn_in_tokens` + `session_in_tokens`
      sum (growing re-send visible); `grade_agent` writes both into the trace entry
      + tests (test_agent.py pattern, growing fake replies)
      depends_on: T1
      refs: R3

- [ ] T4: Dim-result rollups: `avg_in_tokens`/`median_in_tokens` (tools, code) and
      `avg_session_in_tokens`/`median_session_in_tokens` (agent), over all
      non-excluded calls across runs + tests
      depends_on: T2, T3
      refs: R4

- [ ] T5: `report.receipts(r)` + CLI scoreboard `=== Context receipts (tokens sent) ===`
      table ('?' for legacy rows) + test_report tests; score paths untouched
      depends_on: T4
      refs: R5

- [ ] T6: HTML: `_rows` carries receipts; `Context receipts` table section after
      Tokens per second, '?' with the `miss` class; `_pack`/sort keys untouched
      + test_html_report tests
      depends_on: T5
      refs: R5

- [ ] T7: Docs: SPEC §4.2/§4.4/§4.6 + new §4.7 Context receipts; ADR-0011
      (receipts are metadata, not a condition) in harness/decisions/;
      traceability check + harness/init.sh green + request Completion Gate
      depends_on: T6
      refs: R6, R7
