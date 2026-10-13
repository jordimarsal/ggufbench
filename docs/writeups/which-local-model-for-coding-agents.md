# Which local model should a coding agent run? Nine GGUFs, one harness, receipts

I run coding agents on my own hardware. llama.cpp on two RTX 5080s, models from my `models` folder, and one question: which GGUF, at which quant, should I load before I start working?

Public leaderboards measure something else. They are mostly trained on, they score single-shot answers, and they say nothing about whether a model can call a tool with well-formed arguments, survive a multi-call loop, read a folder, edit a file, and verify its own change. That is the work an agent does all day, so I stopped reading those tables for this decision and built [ggufbench](https://github.com/jordimarsal/ggufbench).

One harness, same conditions, four dimensions, and the raw receipts of every call.

## The rules that make the numbers mean something

Every model runs with identical samplings: temperature 0.2, top-p 0.95, seed 42, KV cache q4_0, `--jinja`, one slot. The settings are pinned in two places, the server flags and the request body, so a config drift on the server side cannot leak into a comparison.

Each model keeps its own profile file. That profile is applied last and can override the baseline, so models compete in their real best configuration instead of a lab setup I invented. Infrastructure flags are fixed by the harness, and whatever the model ended up running with is recorded in its result row.

Exclusions are written down with a reason. A model that times out or answers with prose where a code block was expected does not silently disappear from the average; it shows up in the report, counted.

The harness itself uses only the Python standard library. No dependency tree to rot while the benchmark sits.

Every task keeps three runs, seeds 42, 43 and 44, and the scoreboard reports mean ± standard deviation. When a row reads `0.84 ±1`, that spread is part of the answer.

## What the scoreboard said

The current pool ran on harness v3: 12 tool tasks, 60 code tasks, 28 multi-step agent tasks, 32K context, measured on 2026-10-13. The top of the table:

| model | tools | code | agent | speed | global |
| --- | --- | --- | --- | --- | --- |
| gemma-4-26b-a4b-it q5_k_xl | 92% | 91% | 93% | 32ms | 0.84 |
| qwen36-35b-distill mxfp4_moe | 92% | 80% | 82% | 17ms | 0.84 |
| qwen3.8-27b turbo q4_k_s | 92% | 84% | 96% | 45ms | 0.81 |
| strata iq3_xxs | 86% | 88% | 96% | 50ms | 0.80 |

Three things stood out.

### The top rows are ties

The first two models score 0.84 with a spread of ±1. Two tenths of a point separate the top four, well inside their variance. The global score is good for ranking a fleet, and it does not certify that the first row beats the third. Anyone quoting the difference to two decimals is quoting noise.

### Thinking mode hurt

I measured it as a separate pool row instead of folding it into one number. Across a 60-task code bank on 11 models, thinking off excluded 0 of 660 runs; thinking on excluded 14, thirteen of them format failures (an empty reply, a wrong-language fence, prose where code belonged) and one timeout. Latency multiplied: a single speed turn went from 40 to 665 ms. The median run spent 253 extra output tokens to get there. For a coding agent on a token budget, that is a tax with no visible return.

### Easy code tasks don't discriminate

Every serious model passed the trivial tasks, 84% to 100%, which means that dimension was measuring nothing. I added a hard tier (fix, optimise, implement real code) before the scores started to separate. The gap shows up in code before it shows up in tool-calling, which is where I expected the opposite.

## What I would tell you to do

Pick by dimension. If your agent calls tools all day, weight the tools column. If it edits code, use the hard tier and ignore the easy one. If it chains steps, the agent column is your number.

Measure on your own hardware with your own profile files. A quant that is comfortable on two 5080s is a slideshow on one, and the picture changes with the KV cache settings.

Read the exclusions. A model that occasionally fails to format a tool call is not slightly worse than one that always does. In an agent loop it stops the loop.

Treat close rows as ties. My own table has four models inside a point of each other. I pick between them on speed and on how they behave when a tool call fails, not on the third decimal of a benchmark score.

## The fine print

The tasks are written for this harness, the reference solutions never leave the machine, and the models under test are the consumer-GPU quants people run. The scores answer "which GGUF should I run for agentic work", not "how smart is this model". Full method in the repo's `docs/SPEC.md`.

Scoreboard and live report: [jordimarsal.github.io/ggufbench](https://jordimarsal.github.io/ggufbench/).
Code, tasks and receipts: [github.com/jordimarsal/ggufbench](https://github.com/jordimarsal/ggufbench).
