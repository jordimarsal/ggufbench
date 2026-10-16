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

**Three task sets live in the pool** — the suite grew and older rows were measured under
earlier ones. A score is comparable **only inside a set**, so every table below is one set
and the full report marks each row with its `SET` badge (`label·task-set`, e.g.
`v3·16/60/60`). Read columns down a table, never rows across tables.

Common to every row: llama-server 0.6.0-dev+4413a19, **3 runs per task, seeds 42/43/44**
(mean ± stdev), 2× RTX 5080. `excl.` = excluded with a recorded reason. 13 models were
retired (9 on 2026-10-13, 1 on 10-14, 3 on 10-15 — `harness/retired.json` has the why):
their rows stay in the full report behind its **Retired** tab — record only, they count
for neither the headline KPIs nor the recommendations. Rows at a model's maximum context
were measured with the desktop idle; the report prints each row's flags (`-c` included),
and Heretic's pin has since come down to its day-safe 147456 (2026-10-16,
`harness/tools/probe-context.py`).

**Current set — 18 tools · 72 code · 72 agent** (v5, 2026-10-14 · fleet re-measured 10-14/15)

| model | think | tools | code | agent | speed | global |
|---|---|---|---|---|---|---|
| minicpm-v-4.7-35b-a3b q4_k_m | on | 100% ±0 | 82% ±4 *(8 excl.)* | 89% ±0 | 23ms | **0.85 ±1** |
| minicpm-v-4.7-35b-a3b q4_k_m | off ★ | 100% ±0 | 83% ±1 *(2 excl.)* | 90% ±2 | 26ms | **0.85 ±0** |
| qwen36-35b-distill-mxfp4_moe | off ★ | 94% ±0 | 74% ±3 | 92% ±2 | 19ms | 0.84 ±1 |
| qwen3.8-27b-ud-q3_k_xl | off | 100% ±0 | 79% ±4 | 90% ±1 | 36ms | 0.82 ±1 |
| ornith-1.5-35b-a3b-apex-mtp-quality | off ★ | 100% ±0 | 75% ±2 | 92% ±1 | 32ms | 0.82 ±1 |
| qwen3.8-27b-heretic-q4_k_m | off ★ | 100% ±0 | 86% ±2 | 92% ±2 | 85ms | 0.81 ±1 |
| qwen3.8-27b-ud-q3_k_xl | on | 94% ±0 | 93% ±1 *(1 excl.)* | 96% ±1 | 629ms | 0.80 ±0 |
| gemma-4-26b-a4b-it-ud-q5_k_xl | off ★ | 89% ±0 | 86% ±1 | 87% ±2 | 33ms | 0.80 ±0 |
| strata-iq3_xxs *(strata engine)* | off ★ | 91% ±6 | 85% ±1 | 92% ±1 | 45ms | 0.80 ±1 |
| qwen3.8-27b-heretic-q4_k_m | on | 94% ±0 | 90% ±2 | 97% ±1 | 1060ms | 0.80 ±0 |
| ornith-1.5-35b-a3b-apex-mtp-quality | on | 94% ±0 | 85% ±2 | 91% ±1 | 506ms | 0.77 ±1 |
| gemma-4-26b-a4b-it-ud-q5_k_xl | on | 91% ±3 | 85% ±3 | 85% ±3 | 775ms | 0.74 ±2 |
| qwen36-35b-distill-mxfp4_moe | on | 93% ±6 | 70% ±4 *(1 excl.)* | 91% ±2 | 280ms | 0.72 ±2 |
| strata-iq3_xxs *(strata engine)* | on | 78% ±0 | 91% ±3 *(4 excl.)* | 77% ±2 | 406ms | 0.70 ±1 |

Six GGUFs and Strata, both thinking modes: that is the fleet re-measure at this set (the
night of 2026-10-14/15). Thinking ON pays for its own thinking tokens in the speed probe —
every ON row but MiniCPM's runs 280-1060ms against 19-85ms OFF (its own lands at 23ms) —
and it costs quality in every model as well, with MiniCPM the only tie. Where it does buy
something is the hard code tier: UD-Q3 +14 points over its own OFF (79→93), Ornith +10,
strata +6, Heretic +4, and Heretic's agent reaches 97%, the fleet's best. Two ON rows are
still owed a fair pass, and the report says so in its condition note: gemma was measured at
the earlier call caps (256/2048 instead of 1024/8192) and Strata at 512 with 51 empty
replies. The rest of the pool below is **superseded**; part of it also predates the grader
fix of 2026-10-14 (§D10 in `docs/MILLORA.md`: shared task ids were attributed across
languages), so read its code/agent numbers with that in mind.

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
