# Design: report_polish

## Files to modify

| File | Change |
|---|---|
| `html_report.py` | `render()`: split rows into live/retired; build the board content (KPI strip + Recommendations + sections) and, when retired rows exist, wrap it with the retired pane behind pure-CSS radio tabs. Extract `_kpis(rows)`, `_dim_bars(rows, key, fmt)`, `_sections(rows, sort, *, board)`; `_by_set_section(rows, *, anchors=True)`; flip the dimension-list sort; header chips (models count, task-set links, drop the "gray = …" chip); `_CSS` grows the `.tabs` block. |
| `tests/test_html_report.py` | New `TestReportTabs` + order assertions; update the three tests that pin the old layout (think-mode regions, retired chip, no-retired case). |
| `README.md` | The retired note ("rows stay in the full report, grayed, as a record") → "in a Retired tab of the report". |
| `harness/decisions/0010-report-ui-without-javascript.md` | Written with this spec (ADR: report UI stays JavaScript-optional). |

## New signatures

```python
# html_report.py
def _kpis(rows): ...                  # the <div class="kpis"> strip (values from `rows`)
def _dim_bars(rows, key, fmt): ...    # best→worst: scores/tps desc, speed_ms asc; None at the end
def _by_set_section(rows, *, anchors=True): ...  # anchors=False → blocks without id=
def _sections(rows, sort, *, board): ...         # ranking (+sortbar if board) + sets
                                                 # (+anchors if board) + dims + t/s + matrix + details
def _tabbar(live_n, retired_n): ...   # the two <label>s (counts in them)
def _retired_pane(rows): ...          # note + _sections(rows, "global", board=False)
```

`render(pool, sort="global")` keeps its signature and its contract (static order +
optional reorder control). Assembly sketch:

```python
rows = _order_rows(_rows(pool), sort)
live = [r for r in rows if not r["retired"]]
gone = [r for r in rows if r["retired"]]
board = _kpis(live) + "\n" + _rec_section(live) + "\n" + _sections(live, sort, board=True)
body = board if not gone else _tabs_html(board, _retired_pane(gone), len(live), len(gone))
```

The retired pane always renders in `global` order (the order control is a board tool).

## DOM contract (what the tests pin)

```html
<div class="tabs">
<input type="radio" name="board" id="tab-board" checked>
<input type="radio" name="board" id="tab-retired">
<nav class="tabbar" aria-label="board views">
  <label for="tab-board">Board <b>18</b></label>
  <label for="tab-retired">Retired <b>16</b> · record only</label>
</nav>
<div class="pane-board">…kpis · recommendations · sections…</div>
<div class="pane-retired">
  <p class="miss">Record only: these models were retired from the bench and cannot run
  again; their rows stay for history (see <code>harness/retired.json</code>).</p>
  …sections…
</div>
</div>
```

- The wrapper exists only when `gone` is non-empty (R3); `id="tab-board"` carries the
  literal `checked` attribute (R2).
- `id="ranking"`, `id="sortkey"`, `id="sorted"` occur exactly once (board pane);
  `id="set-*"` anchors occur only in the board pane (R11).
- CSS (in `_CSS`, next to `.sortbar`):

```css
.tabs{display:grid;gap:12px;position:relative}
.tabs>input{position:absolute;opacity:0;pointer-events:none}
.tabbar{display:flex;gap:6px}
.tabbar label{cursor:pointer;font:12px/1 var(--mono);color:var(--muted);
  border:1px solid var(--border);border-radius:999px;padding:6px 10px;background:var(--card2)}
.tabbar label b{color:var(--text)}
#tab-board:checked~.tabbar label[for="tab-board"],
#tab-retired:checked~.tabbar label[for="tab-retired"]{color:#fff;background:var(--primary);border-color:transparent}
#tab-board:focus-visible~.tabbar label[for="tab-board"],
#tab-retired:focus-visible~.tabbar label[for="tab-retired"]{outline:2px solid var(--accent);outline-offset:2px}
#tab-board:checked~.pane-retired{display:none}
#tab-retired:checked~.pane-board{display:none}
.pane-board,.pane-retired{display:grid;gap:16px}
```

## Chips (header)

- models: `<b>{len(live)}</b> models` + ` (+{len(gone)} retired)` when `gone` (R10).
- the `gray = retired model (record only)` chip is removed; the tab label and the pane
  note carry that information (R9).
- task sets: iterate `R.ordered_signatures(pool)` as today, but link `#set-…` only when
  the signature is in `{r["sig"] for r in live}`; otherwise `<span class="miss">sig</span>` (R11).
- banner, weights, engines/baselines/caps chips, GPUs, measured span, compare link:
  unchanged (global to the pool, above the tabs).

## Ordering flip (R7)

`_dim_bars` sort key becomes:

```python
def key(x):
    v = x["sc"][key]
    return (v if v else 1e9) if key == "speed_ms" else -(v or 0)
```

Descending scores/tps, ascending ms; a row without the measurement (`None`/0) lands at
the end of the list, where before it landed at the top. Ties keep pool order (stable
sort on rows already in global-desc order). The Weighted-global ranking, the by-set
blocks, the language matrix and the per-model details are already best→worst and stay.

## Error cases

- Pool with retired rows only (`live == []`): board pane renders the KPI placeholders
  (`—` / `0`), empty lists and no cards — same tolerance as the empty pool today; no
  special-casing, no crash (`_rec_section` already returns `""` without cards).
- Rows with `speed_ms`/scores missing: the flipped keys treat them as worst, never crash.
- `models/retired/` + registry absent or broken (CI): `_retired_stems()` → empty set →
  R3 layout (existing tests already cover the lookup).

## Discarded alternative

**JavaScript tab controller** (buttons + `role="tab"` + `location.hash` deep-links).
Rejected: it adds a second inline `<script>` — breaking the `<=1 script` test and the
offline-first promise — and with JS off one pane becomes unreachable, while today the
whole page is readable without JS. Pure-CSS radio tabs give keyboard-operable switching
with zero new script; the ARIA-tab role model is the price (accepted, ADR-0010).

## Tests

Updates to existing tests (they pin the old layout; keep names — `--all` stays green):

- `test_every_model_row_shows_think_mode` (l.97): the Recommendations moved, so the old
  `partition("Recommendations (by use)")` boundary is wrong. Count `think:off`/`think:on`
  (9 each, unchanged) in the body after `<h2>Weighted global</h2>`; keep asserting both
  modes inside the cards region (between `Recommendations (by use)` and that heading).
- `TestRetiredGray.test_retired_row_is_gray_with_badge`: row + badge still present (now
  inside `pane-retired`); the removed chip's assertion becomes the pane note
  (`Record only`) + `class="pane-retired"`.
- `TestRetiredGray.test_registry_greys_rows_without_archived_profiles`: same swap
  (`gray = retired model…` → `class="pane-retired"` + `Record only`).
- `TestRetiredGray.test_non_retired_unchanged`: add `assertNotIn('class="tabs"', html)`.

New tests:

- `test_two_panes_when_retired_exist` (R1, R8): live `foo` + retired `bar` → `class="tabs"`,
  both radios, both panes; board split (before `class="pane-retired"`) contains `foo`, no
  `bar`, no `trow retired`; retired split contains `bar`, no `foo`.
- `test_board_tab_checked_by_default` (R2): `'id="tab-board" checked'` present,
  `'id="tab-retired" checked'` absent.
- `test_pure_css_switching` (R12): the two `:checked~.pane-…{display:none}` rules present;
  `html.count("<script") <= 1` (keeps the existing self-contained test too).
- `test_retired_pane_has_no_recs_nor_kpis` (R4): retired split has no
  `Recommendations (by use)` and no `class="kpis"`.
- `test_kpis_ignore_retired_rows` (R5): retired row with gen 999 t/s / 1 ms; board's
  `.kpis` div shows the live values, `999` absent from it; `999 t/s` present in the
  retired pane.
- `test_recommendations_below_the_kpis` (R6): indexOf ordering
  `<div class="kpis">` < `Recommendations (by use)` < `<h2>Weighted global</h2>`.
- `test_dim_lists_best_first` (R7): three rows (code .9/.5/.1, gen 300/200/100, speed
  10/100/1000) → within each section, indexOf best < worst (code/gen desc, speed asc);
  repeat with a retired pair to cover the retired pane.
- `test_models_chip_counts_live_and_retired` (R10): `models (+1 retired)` with a retired
  row; absent without.
- `test_tasksets_chip_links_only_board_blocks` (R11): three distinct signatures (two
  live, one retired-only) → `href="#set-<live>"` present, `id="set-<retired>"` and
  `href="#set-<retired>"` absent, retired signature still named (chip text + retired
  pane block).

## Architectural Decisions

### ADR-1: retired pane is the board mirror minus judgments
**Context:** retired rows are noise in the live board, but the report is also their only
complete record; dropping them from the sections would lose data.
**Decision:** the Retired pane renders the same sections computed on retired rows only;
it carries no KPI strip and no Recommendations (those are choice instruments and retired
models cannot be chosen).
**Alternatives considered:** a compact single table (loses the per-dimension record);
keeping retired interleaved with a filter (the noise stays in the reading path).
**Consequences:** ~15 % more markup in the published page; every future section addition
must render for both row sets (the helpers already take `rows`).

### ADR-2: tabs with native radios + CSS, no new script
**Context:** the report ships one inline script and must read without JS; a JS tab
controller would be the obvious implementation.
**Decision:** `<input type="radio">` + `<label>` + `:checked~` CSS switch the panes;
default `checked` is Board.
**Alternatives considered:** JS controller (second script, JS-off panes unreachable);
`<details>` disclosure (human asked for a tab; an open record buries the board).
**Consequences:** full ARIA tab semantics are out of reach without scripting (accepted;
radios are keyboard-native); recorded in ADR-0010 as the report-wide rule.

### ADR-3: KPIs computed on live rows only
**Context:** "Fastest (gen) 307 t/s / Lowest latency 13 ms" are today won by a retired
model — a headline the reader cannot act on.
**Decision:** the KPI strip is computed from live rows; the retired values stay visible
in the retired pane's own lists.
**Alternatives considered:** pool-wide KPIs (contradicts the noise split); no KPIs at
all (loses the at-a-glance summary the human explicitly keeps).
**Consequences:** the strip changes values the day a model is retired — correct, but
worth a line in the progress log at every retirement.
