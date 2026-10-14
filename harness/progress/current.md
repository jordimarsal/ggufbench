# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_
- **Agent:** _—_

## Plan

_The task set is frozen at v5 (tools 18 · code 72 · agent 72). What is left is the night of
GPU, not the dataset:_

1. **C9 option 1 — the fleet re-measure at v5.** 7 GGUF + Strata, thinking OFF, `--runs 3`,
   one sitting, one frozen tuple: task set 18/72/72 · engine build · KV baseline `q8_0` ·
   OFF. Never llama-server and Strata at the same time (the harness owns the lifecycle).
   Expected: run time grows (the suite is bigger), so plan the whole night; then
   `python3 -m ggufbench.run --scoreboard --html` and `harness/tools/publish-report.sh`.
   The board afterwards should show ONE task set, ONE baseline id (`f982b06a`) and the new
   engine/build axis; §C10's baseline axis starts reporting from the first new row.
2. **Then the three write-ups** (`docs/writeups/*.md`, 3 languages): they still describe the
   C1-era condition (12/60/28, "42 multi-step agent tasks") and their "top rows are ties"
   conclusion leans on numbers the re-measure will replace.
3. **Then the README scoreboard tables** with the measured v5 rows (the current tables mark
   v5 as "no rows measured yet").

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

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json._
