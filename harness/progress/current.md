# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** 14 `refusal_badge` ✅ done (gate 2026-11-15).
  13 `model_onboarding` ✅ done. Següent: model-ci T1-T6 (repo nou, públic).
- **Started:** 2026-11-15
- **Agent:** leader=cloud session · implementer=LOCAL (qwen36-35b: feature 13 R9;
  SC117-Qwen3.6-35B: feature 14 T1 + real probe data)
- **Session log (2026-11-15):**
  - Real-file regression (T1 extra): `skip_payload` double type-read — a float32
    `rope.freq_base` parsed as a bogus value type on the first real HF file. Synthetic
    fixtures never used float32/array kvs. Fixed + regression test with real kv shapes.
  - R9 listing failure implemented by LOCAL qwen36 one-shot (3.4 s); its context-less
    review round hallucinated → reviewer applied the URLError widening.
  - Live probe data: SC117 benign 0/36, format 94.4% → `results/refusal/` canonical.
  - Badge on CLI scoreboard (section, never scored) + HTML (badge refusal with
    tooltip), README note, results/refusal/ gitignored.
- **Next:** completion gate feature 14 → model-ci T1-T6 (repo already scaffolded,
  public at github.com/jordimarsal/model-ci) → economics spec → F26 fleet panel.
- **Gate 14 (2026-11-15):** aprovat per l'usuari. Dades vives: SC117 benign 0/36
  format 94.4% a results/refusal/ (gitignored).
