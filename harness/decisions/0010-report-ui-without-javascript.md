# ADR-0010: Report UI affordances stay JavaScript-optional (pure CSS for report_polish)

- **Date:** 2026-10-16
- **Status:** accepted
- **Feature:** report_polish

## Context

The published report (`results/report.html`) is one self-contained file: inline CSS,
exactly one inline script (the ranking's order control) and no external resource. It
must read with JavaScript disabled — the static render *is* the contract, the script
only reorders what is already there — and a test pins the `<= 1 <script>` budget.
report_polish adds the first real navigation affordance to that page (a Board/Retired
tab split), and the obvious implementation — a small JS controller with buttons and
`role="tab"` — would spend the script budget and leave one pane unreachable with JS off.

## Decision

Navigation in the report is built with native HTML + CSS only: `<input type="radio">`
+ `<label>` pairs and `:checked ~` sibling rules switch the panes; the default
(`checked`) tab is the Board. The report keeps its single inline script, no external
resource, and both panes are reachable with JavaScript disabled.

## Alternatives considered

- **JS tab controller** (buttons + `aria-selected` + hidden panes): rejected — a second
  inline script breaks the self-contained budget (and its test), and one pane becomes
  unreachable with JS off.
- **`<details>` disclosure for the retired block**: rejected — the human asked for a
  peer tab, not a disclosure, and an opened record block would bury the board under it.

## Consequences

Future report navigation (filters, alternate views) must follow the same rule or
supersede this ADR. Full ARIA tab semantics (roving tabindex, `role="tab"`/`tabpanel`)
are not possible without scripting: accepted trade-off for a local, single-file page
whose controls are natively keyboard-operable radios. Cheap to reverse — the panes are
plain `<div>`s and the markup degrades to two sequential sections.
