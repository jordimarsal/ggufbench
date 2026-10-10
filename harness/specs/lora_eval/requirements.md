# Requirements: lora_eval

El banc mesura models nuus, però un fine-tune propi (QLoRA del 27B, MILLORA §6) només
es pot demostrar amb una comparació controlada: **el mateix model, amb i sense
adaptador**, mateix protocol i gates. Avui el harness no té per on passar un LoRA al
llama-server ni com distingir-lo al pool.

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
The comparison nu-vs-LoRA SHALL be elective: the same protocol (dims, langs, levels,
thinking) applies, and no run is started automatically; whoever evaluates launches two
runs with identical options except the adapter.

## R5
The system SHALL NOT modify weights, folding, or score semantics; an adapter run is
just another row with its own conditions metadata.
