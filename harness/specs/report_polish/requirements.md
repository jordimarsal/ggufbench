# Requirements: report_polish

The published report (`results/report.html`) became noisy for the choice it exists to
support: the rows of retired models are interleaved — gray — in every section, and the
Recommendations live at the very bottom, far from the KPI strip they answer. The human
asked for three polish changes (2026-10-16): retired models in their own HTML tab, the
recommendations right under the KPI strip, and every stat list ordered best → worst.

The report is a published, self-contained artifact (inline CSS, one inline script, no
network, reads with JavaScript off): the tabs must not add a second script. Nothing here
touches the pool, the CLI board (`report.py`) or the compare page.

## R1
WHEN the pool holds both live and retired rows, the report SHALL render a tab bar with
two panes — Board (live rows only) and Retired (retired rows only) — both present in the
single document, one visible at a time.

## R2
WHEN the report is opened, the Board pane SHALL be the visible one by default (no
storage, no JavaScript needed to reach it).

## R3
WHILE the pool holds no retired rows, the report SHALL render the board content without
a tab bar and without the retired pane.

## R4
The Retired pane SHALL NOT contain the Recommendations section nor the KPI strip: it is
a record, and a retired model can neither be recommended nor win a live headline.

## R5
The KPI strip (Best overall, Fastest (gen), Lowest latency, Newest model) SHALL be
computed from the live rows only — no headline figure may come from a model that was
deleted.

## R6
The Recommendations section SHALL appear after the KPI strip and before the "Weighted
global" section.

## R7
Within every per-dimension list of the report (code, agent, tools, speed in ms, gen t/s,
prompt t/s) the rows SHALL run from best performer to worst — descending for the
higher-is-better scores and throughputs, ascending for latency — including the lists of
the Retired pane.

## R8
The Board pane SHALL NOT render any retired row (the gray styling and the "retired"
badge stay, inside the Retired pane).

## R9
The Retired pane SHALL state that these models are a record only — retired from the
bench, unable to run again.

## R10
WHILE the pool holds retired rows, the header "models" chip SHALL state the two counts
separately (e.g. `18 models (+16 retired)`); without retired rows it SHALL keep the
single total.

## R11
The "task sets" chip SHALL link only to set blocks rendered in the Board pane; a
signature that exists only among retired rows SHALL be named as text, never as a link
to a block that cannot be seen.

## R12
The report SHALL remain self-contained — no external resource, at most the existing
single inline script — and the two panes SHALL stay switchable with JavaScript disabled
(pure CSS).
