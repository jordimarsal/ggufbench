# Requirements: lora_eval

The bench measures bare models, but an own fine-tune (QLoRA of the 27B, MILLORA §6) can
only be demonstrated with a controlled comparison: **the same model, with and without
adapter**, same protocol and gates. Today the harness has no way to pass a LoRA to
llama-server nor to distinguish it in the pool.

## R1
The system SHALL accept a LoRA adapter for code models served by llama.cpp — declared
via `--lora <gguf>` on the CLI or a `--lora`-style line in the model's `.txt` profile —
and SHALL start the server with the corresponding `--lora` flag. Strata SHALL reject a
LoRA request with a clear error (out of scope there).

## R2
WHEN a run uses a LoRA, the system SHALL record its identifier (file stem) in every
result as `lora` (default: absent for runs without one), and the pool upsert key SHALL
become `(slug, thinking, lora)` so that base and adapter rows coexist. Legacy rows
(without a `lora` field) SHALL keep keying as today.

## R3
The scoreboard and HTML report SHALL label adapter rows (e.g. suffix on the model name
or a badge) without changing the rendering of existing entries, and the empty pool
case SHALL render no recommendations change.

## R4
The comparison bare-vs-LoRA SHALL be elective: the same protocol (dims, langs, levels,
thinking) applies, and no run is started automatically; whoever evaluates launches two
runs with identical options except the adapter.

## R5
The system SHALL NOT modify weights, folding, or score semantics; an adapter run is
just another row with its own conditions metadata.
