# Design: thinking_batches

## Files to modify (flat package, no `src/`)

| File | Change |
|---|---|
| `run.py` | Flag `--thinking on\|off` (default `off`); passes it to `ServerManager`, to the chat body (kwarg) and to `result["thinking"]`. The protocol (dims/langs/levels) untouched. |
| `config.py` | `THINKING_DEFAULT = "off"`; generalize `STRATA_EXTRA_BODY` into a per-mode body constructor: `thinking_body(engine, mode)` → `{"chat_template_kwargs": {"enable_thinking": False}}` when `off`, `{}` when `on` (same channel for both engines). |
| `server.py` | `ServerManager.__init__` accepts `thinking` (only to record in `describe_*`/metadata; the effective control goes through the body, not flags — so no model `.txt` can override it). |
| `report.py` | Upsert/load by `(slug, thinking)`; `_forget_matches` untouched (deletes both modes); Table 1: `THINK` column (`on`/`off`/`—` legacy) + code cell with ` (N excl.)`; Tables 2/3: already-separate rows (one per entry) + mode column/mark on 3. Banner intact. |
| `html_report.py` | Per-row mode badge + `excluded: N/M` line on the card; matrix and ordering intact. |
| `token_budget.py` | Key `_key(dim, slug, thinking, lang, task_id)` + `_schema = 2` in the file: without `_schema` (it was 16384) entries are ignored and rewritten on the next run. |
| `graders.py` | `CODE_MAX_TOKENS = 32768`, `CODE_LADDER = [32768]`; `code_timeout`: same formula, ceiling `600 → 1000` (covers 32768 at 44 t/s: `60 + 32768/44×1.25 = 991 ≤ 1000`; fast models unchanged, the cap only cuts hangs). |

## New signatures

```python
# config.py
THINKING_DEFAULT = "off"
def thinking_body(engine: str, mode: str) -> dict: ...  # {} if on

# run.py
ap.add_argument("--thinking", choices=["on", "off"], default=config.THINKING_DEFAULT)

# token_budget.py
_SCHEMA = 2
def _key(dim, model_slug, thinking, lang, task_id) -> str: ...
```

`result["thinking"]` always present in new results (`"on"`/`"off"`). Slug
(`config.slug`) intact: the model identity does not change, only the upsert key.

## Error cases

- `--thinking bogus` → `argparse` dies (same pattern as `--level`).
- Pool with legacy rows (no `thinking`): render `—`, upsert keeps them until the
  re-measure replaces them (key `(slug, None)` does not collide with `(slug, off)`).
- `token_budgets.json` without `_schema` → ignored entirely (it was 16384) and regenerated.
- Think batch with small budgets (speed/tools 128/256): thinkers will exclude en masse —
  recorded data (R6), not an error.

## Discarded alternative

**Per-model switch (only hybrids in think-batch).** Saves GPU but breaks principle nº 1 (same
protocol for everyone) and introduces a per-model capability list that would need
maintaining. The cost (~2× GPU, already accepted) buys comparability; in
non-thinking models the second batch is a no-op that confirms it.

## Tests (existing ID names that CANNOT be renamed)

`test_formula_floors_ceils_and_falls_back`, `test_scaled_timeout_applied_to_the_single_attempt`,
`test_transient_timeout_still_excludes` (timeout_scaling) and `test_banner_only_with_mixed_dates`
change BODY (new ceiling, new key) but keep their NAME: `--all` must stay green.

## Architectural Decisions

### ADR-1: uniform dual batch instead of per-model toggle
**Context:** need to measure think/no-think without breaking comparability.
**Decision:** both batches run for all models with the same protocol.
**Alternatives considered:** think-batch only for hybrids (discarded: see above).
**Consequences:** ~2× GPU time; non-thinkers give nearly identical rows (control).

### ADR-2: pool key `(slug, thinking)`, not two pools
**Context:** upsert per slug would overlap the batches.
**Decision:** a single table with a `THINK` column; the reader compares like-for-like.
**Alternatives considered:** two `pool-think.jsonl` / `pool-nothink.jsonl` (discarded:
duplicates scoreboard/HTML/forget and the banner would have to reason across files).
**Consequences:** `load_pool`/`save_result`/`forget` change key; the display slug
does not change.

### ADR-3: 32768 in a single attempt, no re-escalation
**Context:** reviewer decision (Q1 starts at 32768).
**Decision:** `CODE_LADDER = [32768]`; no conditional second rung.
**Alternatives considered:** 16384 + retry at 32768 on ceiling (discarded: with
seed/temp fixed the prefix is deterministic — feature 4 history — and the retry
adds dead requests; if the ceiling was thinking, more tokens do not guarantee an
answer).
**Consequences:** every code task pays its worst case once; the clock cap rises to 1000.

### ADR-4: thinking control via the body, not server flags
**Context:** two possible routes (`--reasoning off` vs `chat_template_kwargs`).
**Decision:** kwarg in the body for both engines.
**Alternatives considered:** flag `--reasoning off` on the `ServerManager` (discarded:
model `.txt` files apply LAST and could override it; the body has no such
override channel).
**Consequences:** `ServerManager` only records the mode; behavior is fixed by the
request.
