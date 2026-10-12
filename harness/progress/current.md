# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; 2026-10-10 + post-session ad-hoc work)
- **Started:** _—_
- **Agent:** _—_

## Plan

_Pick the next job (candidates: the out_tokens ON vs OFF analysis promised at the
checkpoint; multi-file agent C4; P0 README/CI from MILLORA)._

## Log


- **Ad-hoc (Oct 11, cont.): ngram (lookup) drafting on UD-Q3** — own copy-heavy probe
  (65-line module + rename): ngram-map-k4v 352.3 t/s vs MTP n4 139.5 (2.5×);
  new text 51.2 vs 113-127 (no gain). Exclusive per server. Profile stays
  MTP n4 (mixed traffic); ngram documented in the skill for editing sessions.
  Technical note: isolated attempts in zsh failed on word-splitting (zsh does not
  split $BASE) — sweeps must run under bash.


- **Ad-hoc (Oct 11, cont.): MTP/split sweep on the fleet** (tools at bin/mtp-sweep.py +
  bin/mtp-probe.py, from the qwen38-mtp repo): tensor-split +25-45% on the 4 splitters
  (udq5/heretic/turbofcf/coder390), n4 winner (+3-6% vs n3), n6 kills prose.
  Flags applied to the .txt files: --spec-draft-n-max 4 + --split-mode tensor (UD-Q3 only n4,
  13 GB almost single-GPU; tensor untested). WARNING: pool rows for these 4
  models are now STALE (serving conditions changed) — re-measure pending whenever
  wanted (not now, human order).


- **Ad-hoc (Oct 11, cont.): Strata 0.1.42 reserve tuning** — res 1400 lost OFF decode
  (89.3 t/s); res 1000 passes the verification and wins everything: OFF 116.1 t/s gen
  (+8%), prefill 169.4 (+17%), 43 ms; ON 125.4 t/s (+14%), 465 ms, 0 excluded, code
  0.93. Final config fixed: reserve 1000. llama-slots skill §6f documented.

- **Ad-hoc (Oct 11): Strata 0.1.41 → 0.1.42** (`./update.sh`, engine recompiled, configs
  intact with the §6g budget). First start failed: the new verification
  (70 MiB arena) did not fit on CUDA0 (PROFILE cache 5232 slots over-committed; auto would
  have set 3745). Fix: `--vram-reserve-mib 1400` in strata-iq3_xxs.json (DETAILS §cache).
  Green smoke: health, models, chat with chat_template_kwargs, clean shutdown.
- **Ad-hoc (Oct 10): Coder390 into the pool** (OFF+ON): "-53% tokens" claim CONFIRMED vs
  27B siblings (2,084 vs 4.2-4.4K tok), 0 exclusions in ON, code ON 0.95. llama-slots
  skill: preferred ON reserve. 0.1.41 strata rows saved to
  harness/logs/remeasure_pool/strata-0.1.41-rows.json before measuring 0.1.42.

- **Ad-hoc (direct human order, outside gates):** out_tokens ON vs OFF analysis
  (659 paired instances) + `fix(html_report)`: readable text in the matrix
  (solid background by luminance, no alpha) + think badge in the 8 per-model sections.
  Suite 189 passed. Commit `d486a5d`. report.html regenerated (22 badges/mode).

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
