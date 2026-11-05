# Design: context_receipts

## Files to modify

| File | Change |
|---|---|
| `client.py` | New pure function `parse_usage(resp)` next to `parse_timings` (no network, parses the response dict only). |
| `graders.py` | `grade_tools` / `grade_code` / `grade_speed`: call `C.parse_usage(resp)` per response and write `in_tokens` into each trace entry (omitted on transport-error entries). `grade_tools`/`grade_code` collect all per-call values across runs; `grade_agent` reads the agent episode's receipts into the trace entry. Dim results gain the R4 rollups (`avg_in_tokens`, `median_in_tokens` for tools/code; `avg_session_in_tokens`, `median_session_in_tokens` for agent). |
| `agent.py` | `run_agent` imports `client` for `parse_usage` (pure function — keeps the `client_mod` fake seam intact) and returns `turn_in_tokens` (list, one value per turn) + `session_in_tokens` (sum over turns with a value; None when no turn has one). |
| `report.py` | New `receipts(r)` helper extracting the three rollups (`tools_in_tokens`, `code_in_tokens`, `agent_session_in_tokens`; None when the row predates the field). Scoreboard gains a `=== Context receipts (tokens sent) ===` table after the tps table. `_scores` untouched (it is the scoring-math seam, typed float). |
| `html_report.py` | `_rows` carries `receipts`; a new `Context receipts` table section (same `<table>` style as By language) after Tokens per second; cells render '?' with the `miss` class when the value is None. `_pack`/sort keys untouched. |
| `docs/SPEC.md` | §4.2 (parse_usage), §4.4 (receipts in the graders + rollups), §4.6 (receipts table), and a new `### 4.7 Context receipts` summarizing the pipeline. |

## New signatures

```python
# client.py
def parse_usage(resp: dict[str, Any]) -> int | None:
    """in_tokens = usage.prompt_tokens; fallback round(prompt_tps*prompt_ms/1000);
    None when neither source is present."""

# agent.py (run_agent result, new keys)
{"turn_in_tokens": list[int | None], "session_in_tokens": int | None, ...}

# report.py
def receipts(r: dict[str, Any]) -> dict[str, float | None]:
    # {"tools_in_tokens": x, "code_in_tokens": x, "agent_session_in_tokens": x}
```

## Error cases

- Response without `usage` and without usable timings → `in_tokens` is None on
  the entry (R1, R2); rollups skip None values.
- Transport-error entries (excluded) → no receipt key, never a fabricated 0
  (same convention as `out_tokens` in `grade_code` today).
- Legacy pool rows without rollups → `receipts()` returns None values; both
  renderers print '?' (R5). No migration, no pool rewrite.
- Empty episode (all turns errored) → `session_in_tokens` None, not 0.

## Discarded alternative

**Adding `in_tokens` to the speed result rollup and the board's speed block**:
R4 scopes rollups to tools/code/agent; speed already fills the tps table and a
half-measured rollup there would invite reading tokens/sent as a speed metric.
The speed trace entries still carry per-call `in_tokens` (R2) for the detail
receipt. Similarly, `_scores` stays untouched: receipts ride in a dedicated
`receipts()` map so the scoring seam keeps its `dict[str, float]` contract.

## Tests

`test_parse_usage_*` (usage hit, timings fallback, both absent → None;
test_client.py pattern), `tools_trace_carries_in_tokens` /
`code_trace_carries_in_tokens_next_to_out_tokens` /
`speed_entry_carries_in_tokens` (fake clients, test_graders.py pattern),
`agent_records_turn_and_session_tokens` + `agent_session_grows_with_history`
(test_agent.py pattern: a fake client whose replies grow → the per-turn list
grows and the sum reflects the re-sent context), rollup tests for the four
means/medians across runs, `receipts_table_renders_and_marks_legacy_rows` and
`html_receipts_section_renders` (test_report.py / test_html_report.py
patterns: '?' for rows without the field, existing rows/scores byte-stable),
plus the no-change guard: existing score/pool tests stay green unchanged.

## Architectural Decisions

### ADR-1: receipts are metadata, not a pool condition
**Context:** `thinking`/`lora` extended the pool key because they change the
measured condition; receipts are an observation OF the same measurement.
**Decision:** no key extension, no upsert invalidation, no `task_signature`
change; new rows simply carry more fields.
**Alternatives considered:** keying by receipt presence (discarded: it would
split identical-condition rows and break the mixed-conditions banner logic).
**Consequences:** old and new rows coexist; the only renderer duty is the '?'
placeholder. Copied to `harness/decisions/0011-context-receipts-not-a-condition.md`.

### ADR-2: parse_usage lives in client.py as a pure response parser
**Context:** `usage.prompt_tokens` is the honest count; the timings fallback
(`prompt_tps * prompt_ms / 1000 ≈ prompt_n`) covers servers that omit usage but
report timings — the same trade `parse_timings` already makes for `predicted_n`.
**Decision:** one pure parser, same file and tolerance style as
`parse_timings`; `agent.py` imports it directly (it never needed `client_mod`
for parsing, only for transport).
**Alternatives considered:** asking each fake/real client module to expose
`parse_usage` (discarded: pollutes every test fake for no gain — the parse is a
pure function of the response dict).
**Consequences:** test fakes stay minimal; one place to extend if a third
source (e.g. streaming usage) appears.

### ADR-3: rollups are mean AND median at result level
**Context:** one pathological task (a model rambling on one prompt) can skew a
mean; the median shows the typical call.
**Decision:** both, flat names (`avg_in_tokens`, `median_in_tokens`,
`avg_session_in_tokens`, `median_session_in_tokens`), computed over all
non-excluded calls across runs (the same all-runs honesty as the section
score).
**Alternatives considered:** mean only (discarded: hides the skew); per-run
rollups (discarded: no acceptance demands them and the trace already carries
the per-call detail).
