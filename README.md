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

9 models, thinking OFF, harness v3 (12 tools · 60 code · 28 agent tasks), ctx 32K,
llama-server 0.6.0-dev+4413a19, **3 runs per task, seeds 42/43/44** (mean ± stdev),
measured 2026-10-13 on 2× RTX 5080. `excl.` = excluded with a recorded reason.
7 models retired 2026-10-13 (flota prima — vegeu `models/retired/`); their rows
stay in the full report as a record. ON-mode rows pending their own pass.

Live rendered report: <https://jordimarsal.github.io/ggufbench/> ·
regenerate locally with `harness/tools/publish-report.sh` after a re-measure.: <https://jordimarsal.github.io/ggufbench/> ·
regenerate locally with `harness/tools/publish-report.sh` after a re-measure.

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| gemma-4-26b-a4b-it-ud-q5_k_xl | off | 92% ±0 | 91% ±3 | 93% ±0 | 32ms | 0.84 ±1 |
| qwen36-35b-distill-mxfp4_moe | off | 92% ±0 | 80% ±2 | 82% ±0 | 17ms | 0.84 ±1 |
| qwen3_8-27b-turbofcfusion-...-mtp-q4_k_s | off | 92% ±0 | 84% ±4 | 96% ±0 | 45ms | 0.81 ±1 |
| qwen3_8-27b-heretic-q4_k_m | off | 92% ±0 | 87% ±4 | 92% ±8 | 67ms | 0.79 ±3 |
| qwen3_8-27b-ud-q3_k_xl | off | 92% ±0 | 76% ±1 | 92% ±8 | 36ms | 0.78 ±2 |
| ornith-1_5-35b-a3b-apex-mtp-quality | off | 92% ±0 | 73% ±0 | 87% ±8 | 29ms | 0.78 ±2 |
| qwen3-vl-8b-instruct-1m-q6_k | off | 92% ±0 | 76% ±1 | 87% ±8 | 36ms | 0.77 ±2 |
| huihui-ornith-1_5-35b-a3b-abliterated_i1-iq3_s | off | 92% ±0 | 72% ±4 | 82% ±0 | 28ms | 0.76 ±1 |
| ornith-1_5-35b-a3b-abliterated-mtpv2-ud-iq4_xs | off | 92% ±0 | 75% ±2 | 77% ±16 | 29ms | 0.76 ±5 |
| strata-iq3_xxs | off | 86% ±5 | 88% ±4 | 96% ±0 | 50ms | 0.80 ±2 |


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
