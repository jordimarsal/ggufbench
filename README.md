# ggufbench

[![CI](https://github.com/jordimarsal/ggufbench/actions/workflows/ci.yml/badge.svg)](https://github.com/jordimarsal/ggufbench/actions/workflows/ci.yml) [![built with harness-standard](https://raw.githubusercontent.com/jordimarsal/harness-standard/main/assets/badge.svg)](https://github.com/jordimarsal/harness-standard) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Agentic benchmark for local GGUF models — speed, tools, code, agent. One harness, receipts included.**

`ggufbench` scores local LLMs the way you actually use them: served on your own rig
(llama.cpp or [Strata](https://github.com/Niko1221/Strata)) and graded on four real
dimensions — **prompt speed, tool-calling, code generation and multi-step agent work** —
under one identical harness, with the raw receipts of every call.

No cloud, no APIs, no puzzles. The scoreboard answers one question:
*which GGUF should I run on my machine for agentic work?*

## Scoreboard

15 models, thinking OFF, harness v3 (12 tools · 60 code · 28 agent tasks), ctx 32768,
**3 runs per task** (mean ± stdev), measured 2026-10-12/13 on 2× RTX 5080.
`excl.` = excluded with a recorded reason. Scores are per-seed sampling
(seeds 42/43/44): the ± is real run-to-run variance, and the table **orders**
models on this harness — it does not certify close ranks.
ON-mode rows + qwen36 pending re-measure (see notes below).

Live rendered report: <https://jordimarsal.github.io/ggufbench/> ·
regenerate locally with `harness/tools/publish-report.sh` after a re-measure.

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| strata-iq3_xxs | off | 86% ±5 | 88% ±4 | 96% ±0 | 50ms | 0.80 ±2 |
| qwen3_8-27b-turbofcfusion-...-mtp-q4_k_s | off | 92% ±0 | 83% ±5 | 94% ±2 | 49ms | 0.80 ±1 |
| gemma-4-26b-a4b-it-ud-q5_k_xl | off | 92% ±0 | 84% ±1 | 95% ±2 | 34ms | 0.82 ±0 |
| qwen3_8-27b-ud-q3_k_xl | off | 92% ±0 | 75% ±8 | 92% ±8 | 36ms | 0.78 ±4 |
| qwen3_8-27b-heretic-q4_k_m | off | 92% ±0 | 85% ±2 | 87% ±10 | 69ms | 0.78 ±2 |
| qwen3_8-27b-ud-q5_k_m | off | 92% ±0 | 78% ±0 | 87% ±10 | 41ms | 0.77 ±3 |
| qwen3-coder-30b-a3b-instruct-ud-q4_k_xl | off | 92% ±0 | 23% ±24 (29 excl.) | 0% ±0 | 18ms | 0.45 ±7 |
| qwen3_8-27b-coder390-efficientthink-...-mtp | off | 92% ±0 | 76% ±5 | 92% ±8 | 46ms | 0.77 ±3 |
| qwen3-vl-8b-instruct-1m-q6_k | off | 92% ±0 | 76% ±1 | 87% ±8 | 37ms | 0.77 ±2 |
| qwen3_8-27b-ud-q4_k_m | off | 92% ±0 | 68% ±3 | 93% ±6 | 38ms | 0.76 ±2 |
| huihui-ornith-1_5-35b-a3b-abliterated_i1-iq3_s | off | 92% ±0 | 71% ±3 | 82% ±0 | 29ms | 0.76 ±1 |
| qwen3_8-27b-ud-q4_k_xl | off | 92% ±0 | 72% ±8 | 82% ±0 | 35ms | 0.75 ±2 |
| nvidia-nemotron-3_5-lightning-30b-a3b-iq4_xs | off | 83% ±0 | 44% ±7 (6 excl.) | 87% ±8 | 13ms | 0.75 ±4 |
| ornith-1_5-35b-a3b-abliterated-mtpv2-ud-iq4_xs | off | 92% ±0 | 74% ±1 | 71% ±6 | 31ms | 0.74 ±1 |
| ornith-1_5-35b-a3b-apex-mtp-quality | off | 83% ±0 | 71% ±1 | 82% ±14 | 30ms | 0.73 ±4 |
| muse-glimmer-30b-kquant-dynamic-q4_k_xl | off | 33% ±8 | 81% ±3 | 93% ±2 | 1408ms | 0.58 ±4 |
```bash
# 1. clone (the repo IS the python package; keep it as ./ggufbench)
git clone https://github.com/jordimarsal/ggufbench ggufbench

# 2. put your GGUF models next to it (../models/*.gguf)

# 3. run the full benchmark on a model (starts llama-server itself)
cd ..
python3 -m ggufbench.run --models ../models/Qwen3.8-27B-UD-Q5_K_M.gguf

# accumulated scoreboard + HTML report
python3 -m ggufbench.run --scoreboard --html   # → scoreboard + ggufbench/results/report.html

# head-to-head compare of two pool rows (slug,think — think defaults to off)
python3 -m ggufbench.run --compare "qwen3_8-27b-ud-q5_k_m,off" "qwen3_8-27b-ud-q5_k_m,on"   # → ggufbench/results/compare.html
```

## The four dimensions

| dim | what it measures | how |
|---|---|---|
| **speed** | prompt processing + generation tok/s | real server timings, 3 samples |
| **tools** | 8 tool-call tasks (arguments, multi-call, error handling) | graded in a sandbox |
| **code** | 36 coding tasks across python/bash/java/typescript (easy + hard + expert) | tests must pass, `excl.` recorded |
| **agent** | multi-step work: fix bugs, build features, use folder context | turn + tool-call accounting |

## One harness, receipts included

- same flags, temperature and seed for every model — the scoreboard is only valid
  because every model runs the exact same harness (v3)
- single reasoning budget (32768 tokens); exclusions are recorded with a reason,
  never silent
- every call leaves a receipt: timings, tool calls, per-task traces
- thinking modes measured separately (`off` / `on`) — never mixed in one number
- 100% local: no cloud, no APIs, no telemetry

## Why it is not comparable with HumanEval (or any public benchmark)

Public benchmarks are trained on. These tasks are written for this harness, the
reference solutions never leave the machine, and the models under test are
consumer-GPU quants of the models people actually run locally. Scores answer
"*which model should I run?*", not "*how smart is it?*". Full reasoning in
[`docs/SPEC.md`](docs/SPEC.md).

## Requirements

- Linux x86_64, NVIDIA GPU(s) (works CPU-only, slower)
- llama.cpp (`llama-server`) — the harness builds/starts it per model
- Python 3.12+ (stdlib only for the harness itself)
- GGUF models (any quant) — optionally [Strata](https://github.com/Niko1221/Strata) as a second engine

## Status & docs

| feature | state |
|---|---|
| offer/question modes, dual-think runs, expert tier, VoiceStudio TTS *(sibling project)* | see `harness/feature_list.json` |
| full design doc | [`docs/SPEC.md`](docs/SPEC.md) |

Agent-facing map: [`AGENTS.md`](AGENTS.md) · License: [MIT](LICENSE)

---

*Named after what it benchmarks: the GGUFs gathering dust in your models folder.*
