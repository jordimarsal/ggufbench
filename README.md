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

**Three task sets live in the pool** — the suite grew and the fleet re-measure under the
current one is still pending. A score is comparable **only inside a set**, so every table
below is one set and the full report marks each row with its `SET` badge
(`label·task-set`, e.g. `v3·16/60/60`). Read columns down a table, never rows across
tables.

Common to every row: thinking OFF unless stated, llama-server 0.6.0-dev+4413a19,
**3 runs per task, seeds 42/43/44** (mean ± stdev), ctx 32K (unless the profile pins
more), 2× RTX 5080. `excl.` = excluded with a recorded reason. 9 models were retired on
2026-10-13: their rows stay in the full report, grayed, as a record.

**Current set — 18 tools · 72 code · 72 agent** (v5, 2026-10-14)

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| minicpm-v-4.7-35b-a3b q4_k_m | off | 100% ±0 | 83% ±1 *(2 excl.)* | 90% ±2 | 26ms | **0.85 ±0** |

One row so far (2× RTX 5080, ctx 131072, 24 min for the three rounds). Its weak spot is the
expert code tier (0.67 vs 0.91 easy / 0.87 hard) and bash (it answers bash prompts with
fences in other languages, which the harness records as exclusions, never as silent
failures). The rest of the pool below is **superseded**, and it was also measured before the
grader fix of 2026-10-14 (§D10 in `docs/MILLORA.md`: shared task ids were attributed across
languages), so its code/agent numbers are skewed: the fleet re-measure at this set is the
next step.

**Superseded — 16 tools · 60 code · 60 agent** (v4: the two rows of 2026-10-14)

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| qwen36-35b-distill-mxfp4_moe | off | 94% ±0 | 76% ±2 | 77% ±3 | 18ms | 0.81 ±0 |
| strata-swift-iq3_xxs | off | 84% ±9 | 77% ±2 | 78% ±5 | 42ms | 0.73 ±4 |

**Superseded — 12 tools · 60 code · 28 agent** (the OFF batch, 2026-10-12/13)

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| gemma-4-26b-a4b-it-ud-q5_k_xl | off | 92% ±0 | 91% ±3 | 93% ±0 | 32ms | 0.84 ±1 |
| qwen3_8-27b-turbofcfusion-...-mtp-q4_k_s | off | 92% ±0 | 84% ±4 | 96% ±0 | 45ms | 0.81 ±1 |
| strata-iq3_xxs | off | 86% ±5 | 88% ±4 | 96% ±0 | 50ms | 0.80 ±2 ★ |
| qwen3_8-27b-heretic-q4_k_m | off | 92% ±0 | 87% ±4 | 92% ±8 | 67ms | 0.79 ±3 |
| qwen3_8-27b-ud-q3_k_xl | off | 92% ±0 | 76% ±1 | 92% ±8 | 36ms | 0.78 ±2 |
| ornith-1_5-35b-a3b-apex-mtp-quality | off | 92% ±0 | 73% ±0 | 87% ±8 | 29ms | 0.78 ±2 |
| qwen3-vl-8b-instruct-1m-q6_k | off | 92% ±0 | 76% ±1 | 87% ±8 | 36ms | 0.77 ±2 |

**Older — 8 tools · 60 code · 24 agent** (the thinking-ON batch, 2026-10-10). Not
reproduced here: a thinking-ON run costs 5-6× the wall clock for worse-or-equal quality
(Strata measured both modes on the same engine), so the fleet default is OFF and no ON
re-pass is planned. The rows stay in the full report.

`★` = optimal thinking mode by data (not worse quality within 0.02 and no more wall
clock; docs/MILLORA.md §C8).

### Task-set lineage

| label | set | what changed |
|---|---|---|
| v1 | base | 8 tools · 36 code (easy) · 24 agent |
| v2 | hard tier | +16 `_hard` code tasks |
| v3 | expert tier | +12 `_expert` code tasks, `EXTRA_FILES` sandbox |
| v4 | superseded | the C3 additions: tools 8→16, agent 24→60 |
| v5 | **current** | the C3+C4 fill: tools 16→18, code 15→18 per language, agent 15→18 per language (13 of them multi-file projects: 5-8 files, `list_files`, 14 turns) |

The label is a name, not the condition: **v3 shipped four different counts**
(8/60/24, 12/60/28, 12/60/36, 16/60/60) because the additions never bumped it. That is
why every row now carries its real set (`task_signature`, derived from the graded traces)
and the report groups and sorts by it:

```sh
python3 -m ggufbench.run --scoreboard --sort version   # CLI: grouped by task set
python3 -m ggufbench.run --scoreboard --html           # report: SET badge + "By task set"
```

Live rendered report: <https://jordimarsal.github.io/ggufbench/> · regenerate locally
with `harness/tools/publish-report.sh` after a re-measure.

## Quickstart

The harness is imported as a package, so every command runs from the **workspace root**
— the directory that holds `ggufbench/` and your `models/`:

```sh
# 1. clone it next to the folder with your GGUFs
git clone https://github.com/jordimarsal/ggufbench.git
cd ggufbench

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
| **tools** | 16 tool-call tasks (arguments, multi-call, error handling) | graded in a sandbox |
| **code** | 60 coding tasks across python/bash/java/typescript (32 easy + 16 hard + 12 expert) | tests must pass, `excl.` recorded |
| **agent** | 60 multi-step tasks: fix bugs, build features, use folder context | turn + tool-call accounting |

## One harness, receipts included

- same flags, temperature and seed for every model — the scoreboard is only valid
  because every model runs the exact same harness, and every row states the task set it
  really ran (`SET`: label·task-set; a score is comparable only inside a set)
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
