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

12 models × 2 thinking modes (off / on), harness v3, measured 2026-10-10/12
on 2× RTX 5080. `excl.` = tasks excluded with a recorded reason (never silent).
Scores are single-sample (n=1 per task, fixed seed): the table **orders**
models on this harness — it does not certify close ranks. Strata rows re-measured today with engine 0.1.43.

Live rendered report: <https://jordimarsal.github.io/ggufbench/> ·
regenerate locally with `harness/tools/publish-report.sh` after a re-measure.

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| `qwen36-35b-distill-mxfp4_moe` | off | 100% | 83% | 100% | 16ms | 0.95 |
| `gemma-4-26b-a4b-it-ud-q5_k_xl` | off | 100% | 88% | 100% | 33ms | 0.89 |
| `qwen3_8-27b-ud-q3_k_xl` | off | 100% | 87% | 100% | 33ms | 0.88 |
| `qwen3_8-27b-turbofcfusion-735-882-here-uncen-neo-coder-max-mtp-q4_k_s` | off | 100% | 88% | 100% | 42ms | 0.87 |
| `ornith-1_5-35b-a3b-abliterated-mtpv2-ud-iq4_xs` | off | 100% | 85% | 92% | 31ms | 0.86 |
| `qwen3_8-27b-coder390-efficientthink-q4lynnstyle-mtp` | off | 100% | 85% | 100% | 44ms | 0.86 |
| `huihui-ornith-1_5-35b-a3b-abliterated_i1-iq3_s` | off | 100% | 82% | 92% | 32ms | 0.85 |
| `qwen3_8-27b-ud-q5_k_m` | off | 100% | 82% | 96% | 40ms | 0.84 |
| `qwen3_8-27b-coder390-efficientthink-q4lynnstyle-mtp` | on | 100% | 95% | 100% | 681ms | 0.84 |
| `strata-iq3_xxs` | off | 100% | 92% | 100% | 46ms | 0.88 |
| `qwen3_8-27b-heretic-q4_k_m` | off | 100% | 87% | 100% | 92ms | 0.84 |
| `qwen3_8-27b-ud-q5_k_m` | on | 100% | 96% (4 excl.) | 96% | 665ms | 0.83 |
| `qwen3_8-27b-ud-q3_k_xl` | on | 100% | 95% (2 excl.) | 96% | 629ms | 0.83 |
| `qwen3_8-27b-turbofcfusion-735-882-here-uncen-neo-coder-max-mtp-q4_k_s` | on | 100% | 92% (1 excl.) | 100% | 1707ms | 0.83 |
| `strata-iq3_xxs` | on | 100% | 93% | 96% | 578ms | 0.82 |
| `ornith-1_5-35b-a3b-apex-mtp-quality` | on | 100% | 92% (1 excl.) | 92% | 388ms | 0.81 |
| `huihui-ornith-1_5-35b-a3b-abliterated_i1-iq3_s` | on | 100% | 90% | 92% | 403ms | 0.81 |
| `qwen3-vl-8b-instruct-1m-q6_k` | off | 100% | 73% | 88% | 37ms | 0.80 |
| `qwen3-vl-8b-instruct-1m-q6_k` | on | 100% | 73% | 88% | 37ms | 0.80 |
| `ornith-1_5-35b-a3b-apex-mtp-quality` | off | 88% | 80% | 88% | 30ms | 0.80 |
| `qwen36-35b-distill-mxfp4_moe` | on | 100% | 78% (5 excl.) | 96% | 186ms | 0.79 |
| `ornith-1_5-35b-a3b-abliterated-mtpv2-ud-iq4_xs` | on | 88% | 93% | 96% | 613ms | 0.79 |
| `qwen3_8-27b-heretic-q4_k_m` | on | 100% | 90% (1 excl.) | 83% | 1515ms | 0.78 |
| `gemma-4-26b-a4b-it-ud-q5_k_xl` | on | 75% | 87% | 88% | 897ms | 0.71 |

## Quick start

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
