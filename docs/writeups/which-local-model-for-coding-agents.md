# Which local model should a coding agent run? Seven GGUFs and a Strata engine, one harness, receipts

*Also available in [Spanish](which-local-model-for-coding-agents.es.md) and [Catalan](which-local-model-for-coding-agents.ca.md).*

I run coding agents on my own hardware. llama.cpp on two RTX 5080s, models from my `models` folder, and one question: which GGUF, at which quant, should I load before I start working?

Public leaderboards measure something else. Most of their tasks are in models' training data, they score single-shot answers, and they say nothing about whether a model can call a tool with well-formed arguments, survive a multi-call loop, read a folder, edit a file, and verify its own change. That is the work an agent does all day, so I stopped reading those tables for this decision and built [ggufbench](https://github.com/jordimarsal/ggufbench).

One harness, same conditions, four dimensions, and the raw receipts of every call — this round, seven GGUFs under llama.cpp plus one model under the [Strata](https://github.com/Niko1221/Strata) engine, each in both thinking modes.

## The rules that make the numbers mean something

Every model runs with identical sampling: temperature 0.2, top-p 0.95, top-k 40, min-p 0.05, seed 42, KV cache q8_0, `--jinja`, one slot. Every sampler value is pinned explicitly, because a GGUF carries its own sampling metadata — this fleet alone ships three different `top_k` settings (20, 64, and none at all) — and an unpinned value is not a shared condition but a per-model one. The settings are fixed in two places, the server flags and the request body, so config drift on the server cannot leak into a comparison.

Every model keeps its own profile file. That profile applies last and can override the baseline, so models compete in their best real configuration and not in a lab rig I invented. The harness fixes the infrastructure flags, and what each model ended up running with is recorded in its result row.

Exclusions are annotated with a reason. A model that runs out of time or answers with prose where a code block was expected does not silently vanish from the average; it shows up in the report, counted.

The harness uses only the Python standard library. No dependency tree to rot while the benchmark waits.

Every task stores three runs, seeds 42, 43 and 44, and the scoreboard reports mean ± standard deviation. When a row says `0.85 ±1`, that spread is part of the answer.

## What the scoreboard said

The current pool runs set v5: 18 tool tasks, 72 code tasks across four languages (32 easy, 20 hard, 20 expert), 72 multi-step agent tasks (13 of them multi-file projects) and a 32K output budget for code. The rows below are the current pool, task set v5. The table is generated from the live scoreboard, so it is never a snapshot of a night that has passed.

<!-- table:start -->
| model | think | tools | code | agent | speed | global |
| --- | --- | --- | --- | --- | --- | --- |
| minicpm-v-4.7-35b-a3b q4_k_m | on | 100% ±0 | 82% ±4 *(8 excl.)* | 89% ±0 | 23ms | **0.85 ±1** |
| minicpm-v-4.7-35b-a3b q4_k_m ★ | off | 100% ±0 | 83% ±1 *(2 excl.)* | 90% ±2 | 26ms | **0.85 ±0** |
| qwen36-35b-distill-mxfp4_moe ★ | off | 94% ±0 | 74% ±3 | 92% ±2 | 19ms | **0.84 ±1** |
| qwen3.8-27b-ud-q3_k_xl | off | 100% ±0 | 79% ±4 | 90% ±1 | 36ms | 0.82 ±1 |
| ornith-1.5-35b-a3b-apex-mtp-quality ★ | off | 100% ±0 | 75% ±2 | 92% ±1 | 32ms | 0.82 ±1 |
| qwen3.8-27b-heretic-q4_k_m ★ | off | 100% ±0 | 86% ±2 | 92% ±2 | 85ms | 0.81 ±1 |
| qwen3.8-27b-neo-coder-max-mtp q4_k_s | off | 100% ±0 | 79% ±2 | 91% ±1 | 46ms | 0.81 ±0 |
| qwen3.8-27b-ud-q3_k_xl | on | 94% ±0 | 93% ±1 *(1 excl.)* | 96% ±1 | 629ms | 0.80 ±0 |
| gemma-4-26b-a4b-it-ud-q5_k_xl ★ | off | 89% ±0 | 86% ±1 | 87% ±2 | 33ms | 0.80 ±0 |
| strata-iq3_xxs *(strata engine)* ★ | off | 91% ±3 | 84% ±1 | 91% ±2 | 40ms | 0.80 ±1 |
| qwen3.8-27b-heretic-q4_k_m | on | 94% ±0 | 90% ±2 | 97% ±1 | 1060ms | 0.80 ±0 |

*★ = each model's optimal thinking mode by data: quality within ±0.02 of the other mode and no extra wall clock; exact ties go to off.*
<!-- table:end -->

Four things stood out.

### The top rows are ties

The top ten rows span five hundredths of a point — 0.85 down to 0.80 — and neighbouring rows sit at most one or two hundredths apart, the same size as the run-to-run spread printed beside each score. The global score ranks a fleet; it does not certify that row 1 beats row 7. Anyone ranking two close rows by their second decimal is quoting noise.

### Thinking mode is a tax that only pays in hard code

I measured it as separate rows instead of folding it into one number. Thinking ON multiplies turn latency — every ON row but MiniCPM's runs 280–1060 ms against 19–85 ms OFF (MiniCPM's ON lands at 23 ms) — and it costs quality in every model as well, with MiniCPM the only tie. It also concentrates the exclusions: across the fleet's 1,512 code runs per mode, OFF excludes 6 and ON excludes 101, most of them answers with no code block where one was expected (fully excluded tasks: 2 against 14).

Where it does buy something is the hard code tier: UD-Q3 climbs from 79% to 93% on code overall (92% hard, 91% expert), Ornith +10 points over its own OFF, strata +7, Heretic +4 — and Heretic's agent loop reaches 97%, the fleet's best. On the tasks that need it, thinking is worth ten times the wait; everywhere else it is a tax with no visible return.

### Easy code tasks don't discriminate

With thinking off the entire fleet lands between 91% and 100% on the easy tier, while hard and expert live between 47% and 87%. Those two levels are where the separation is — especially the expert ones, built from multi-bug debugging with strict output contracts (return the full corrected file, exact rounding, defensive copies). The scoreboard folds all three levels into one code column; the per-level breakdown it records (`by_level`) is where the arguments happen.

### The engine was not the variable

I ran the same harness against a different engine, the community MoE streaming engine
[BigMoeOnEdge](https://github.com/Helldez/BigMoeOnEdge), to see whether the engine decides the
score. It did not: 0.920 against 0.923 on the same 72 agent tasks, same model, same quant, at
the same throughput (48 tok/s against 47). For a 27B on two 5080s, streaming experts from NVMe
is not the bottleneck.

Two conditions, so the comparison is honest. The engine ran at a 16K context, because a
32K-wide prefill graph wants a 19.2 GB compute buffer and does not fit a 16 GB card. And it
has no knob for the KV cache type, so the KV was the engine's default rather than the q8_0 the
rows above pin. The seed is a session parameter there, so it was set per run and the session
reloaded.

What it did surface is a bug in that engine's router hook. A generated turn that its chat
parser cannot turn into text or a tool call comes back as an empty assistant message: 31
tokens generated, the turn dropped, and the episode carries on with a hole in it. Twelve of
those in the three runs, and two bash tasks flip from pass to fail because of it. llama.cpp
recovers where the other one drops the turn, so the same model and the same prompts produce no
empty reply there. Filed with a backtrace:
[issue #334](https://github.com/Helldez/BigMoeOnEdge/issues/334).

## What I would tell you to do

Pick by dimension. In this table, tools belong to MiniCPM (100%), hard code to UD-Q3 with thinking (92% hard, 91% expert), the agent loop to Heretic with thinking (97%), and per-turn speed to qwen36 off (19 ms). No row wins everything.

Measure on your own hardware with your own profiles. A quant that is comfortable on two 5080s is a slideshow on one, and the result changes with the KV cache configuration.

Read the exclusions. A model that fails to format a tool call once in a while is not slightly worse than one that never misses. In an agent loop, it stops.

Treat close rows as ties. Ten rows inside five hundredths of a point is not a ranking, it is a group. I choose inside it by latency and by how a model behaves when a call fails, not by the third decimal of a score.

Do not look for the bottleneck in the engine first. The same harness against a different engine moved the score by three thousandths and the throughput by one token per second.

## The fine print

The tasks are written for this harness, the reference solutions never leave the machine, and the models under test are the consumer-GPU quants people actually run. Scores answer "which GGUF should I run for agentic work", not "how smart is this model". Two thinking-ON rows (gemma, strata) were measured under tighter tool-loop caps than the rest and are flagged in the report as owed a fair pass; the thirteen models retired along the way live in its Retired tab, record only. The table above is generated from the live scoreboard, not typed in, and the engine comparison ran under the conditions stated in its section. Full method in `docs/SPEC.md` of the repository.

Live scoreboard and report: [jordimarsal.github.io/ggufbench](https://jordimarsal.github.io/ggufbench/).
Code, tasks and receipts: [github.com/jordimarsal/ggufbench](https://github.com/jordimarsal/ggufbench).
