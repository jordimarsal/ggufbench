# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_
- **Agent:** _—_

## Plan

_The task set is frozen at v5 (tools 18 · code 72 · agent 72) and the sampler is pinned in the
baseline (`ed3153c0`), so what is left is a night of GPU: the holes on the board are
conditions, not data. Sequence fixed with the human (2026-10-14), running detached:_

1. **Dense fleet, thinking OFF, at v5** — Heretic, TurboFCFusion, UD-Q3_K_XL, Qwen3-VL-8B,
   `--runs 3`. Running; log `harness/logs/v5_off/dense.log`. Upserts the four dense rows.
2. **Strata: calibrate the engine, then OFF, then ON.** `./setup.sh --calibrate` measures the
   four PC-dependent settings (the share of missed experts copied over PCIe instead of computed
   by the CPU, the draft confidence, the CPU pool threads, the VRAM expert cache) and writes
   them **into the config's args** — so they land in `model_config_flags` of every row measured
   after it (the §C9 lesson: a condition that differs must be visible in the row). Calibrate
   both configs (`iq3_xxs`, `swift-iq3_xxs`), then OFF ×3 on both and ON ×3 on `iq3_xxs` (the
   ★ optimal-mode marker needs the pair; the swift row has no ON counterpart in the pool).
3. **Fleet ON at v5** — 8 GGUF (3 MoE + MiniCPM + the 4 dense) with `--thinking on` and the
   per-call caps raised **for the whole batch**, the same value in every row: `--tools-max-tokens
   256 --agent-max-tokens 1024`. The 128-token cap is measurably too tight (Heretic's OFF run
   hit it twice on `refuse_delete_protected`). The code budget stays 32768 so the ON/OFF pair
   is not confounded by anything but the mode.
4. **Then the paperwork**: `--scoreboard --html` + `harness/tools/publish-report.sh`, the three
   write-ups (`docs/writeups/*.md`) and the README tables, which still describe the C1-era
   condition (12/60/28, "42 multi-step agent tasks").

## Log

- **2026-10-14 · New model preview: MiniCPM-V 4.7 35B-A3B (OpenBMB, human order).** The tweet
  (2026-10-12) announces the MiniCPM-V 4.7 series; the 35B-A3B is the first MoE of the family
  (on-device MLLM, LES lookahead expert scheduling, Apache-2.0). Checked before downloading:
  the GGUF declares arch **`qwen35moe`**, which this repo's llama.cpp (0.6.0-dev+4413a1924)
  supports — `llama_model_qwen35moe` + `src/models/qwen35moe.cpp` are in libllama.so, MTP
  branch included. Header read over HTTP range (no download): ctx 262144, 40 blocks with
  `full_attention_interval 4` (hybrid SSM/attention), GQA 2/16 with key/value length 256 →
  KV is cheap (~1.5 GB at 128k, q8_0), 256 experts / 8 active, **no MTP tensors** (their
  speculative path is the separate DSpark draft + LES fork), and the chat template honours
  `enable_thinking: false` → the harness's OFF mode is a clean instruct run.
  Downloaded `MiniCPM-V-4_7-35B-A3B-Q4_K_M.gguf` (21.2 GB) with `hf download` into
  `models/`, plus the profile `models/MiniCPM-V-4_7-35B-A3B-Q4_K_M.txt` (`-c 131072`: the
  32768 code budget must fit with the prompt; sampling stays the harness baseline).
  Run: `--models models/MiniCPM-V-4_7-35B-A3B-Q4_K_M.gguf --runs 3` (thinking OFF, the pool
  protocol), log in `harness/logs/minicpm_v47/`.
- **2026-10-14 · First run done (24 min) — and it found a grader bug, not a model trait.** The
  row came out `tools 1.000 ±0 · code 0.571 ±4 · agent 0.895 ±1 · 18→23 ms · global 0.826 ±1`
  with a nonsense level breakdown (`easy 0.44 < hard 0.75`) and a bash-only language pattern.
  Reading the trace showed java/python/typescript tasks recorded as `bash` entries: the
  multi-run aggregation looked entries up by `id`, and ids are unique per *dimension*, not per
  language (the easy tier mirrors `bubble_sort` etc. across the four) — so every shared id took
  bash's outcome. The same refactor had also hardcoded `grade_agent`'s `by_lang` to `{}` and
  dropped `lang` from the agent trace. Fixed (MILLORA §D10, commit 53779ba) with 5 regression
  tests; SPEC §4.4 + AGENTS §3 now state the identity rule. **Consequence: every existing row's
  code/agent score is skewed — the C9 re-measure is the only way to valid numbers**, and the
  MiniCPM row was re-measured right after the fix (log `batch-off-runs3-fixed.log`).
  Tweets aside, the interesting part: the model itself looks strong on tools/agent and weak on
  bash (it answers bash prompts with rust/python fences → exclusions), which the fixed grader
  will now attribute to the right language.
- **2026-10-14 · Sampler settled with data, not doctrine (baseline `f982b06a` → `ed3153c0`).**
  The Ornith A/B: A (temp 0.2 / top_k 40, the harness baseline) against B (temp 1.0 / top_k 20,
  the author's card) gave **0 of 72** code verdict flips with identical code tokens (16,433) and
  2 of 72 agent flips (0.928 → 0.918, inside the ±). So the sampler stays pinned in the baseline
  and (B) remains available as an explicit per-profile option. Receipts: the two
  `results/runs/20261014-*ornith*-off.json` files. Rows measured before the pin keep the old id
  and the board flags them — the reason the dense/MoE OFF rows are re-measured tonight.
- **2026-10-14 · LFM2.5-24B-A2B retired (human decision) — and the reason is a harness lesson.**
  Its chat template always opens a `<think>` block and has no `enable_thinking` switch, so the
  harness's OFF mode was impossible for it and the reasoning ate the per-call budget: 0.59 global
  (tools 78 / code 74 / agent 51). A focused re-run with 256/2048-token caps lifted tools to ~91%
  and the agent to ~75% at half of the dimension — better, still under the fleet's 87-93%. The
  GGUF and its profile are deleted; the stem is in `harness/retired.json` so its pool row stays as
  a record and renders gray (`7a73168`).
- **2026-10-14 · Probes and traceability, so that no condition can hide.** Every row now carries
  `code_budget` / `code_budget_stored` and `ctx_resolved` + `ctx_source`, and the harness probes
  the run itself (`code_budget_hits`, `tools_capped`, `agent_empty_replies`,
  `thinking_mode_applied` via `/props`, with a `probes:` line on the model card). Live proof
  today: the LFM pass warned on 7 truncated tool calls and 5 empty agent turns, and Heretic's OFF
  run warned twice on the 128-token tool cap — which is the evidence behind the 256/1024 caps of
  the ON batch. Legacy `token_budgets.json` entries (37 rows, 4096/8192) are inert: no `_schema: 2`.
- **2026-10-14 · Strata was calibrated — with the engine of 2026-10-01.** Checked
  `~/.config/strata/settings.json`: the calibration ran on 2026-10-01 for
  `qwen3.8-flash-next-iq3_xxs|131072` and kept a single setting, `--pool-workers 4` (65.5 t/s
  then), which is the value our config carries. That day's engine is not today's (0.1.44.1), so
  the measurement is re-run as the first Strata step of the night. `--calibrate` rewrites only the
  config's args and the settings file — it never reinstalls — and `--yes --no-start` makes it
  non-interactive without leaving a server up.

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json. The night's benches run
detached (`setsid`): check `harness/logs/v5_off/dense.log`, `harness/logs/v5_strata/` and
`harness/logs/v5_on/fleet.log` before touching anything, and never start a server while one is up
— the harness owns the lifecycle._
