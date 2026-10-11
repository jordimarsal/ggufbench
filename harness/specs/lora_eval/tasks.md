# Tasks: lora_eval

- [ ] T1: `--lora` CLI + `.txt` profile → `build_args` (`--lora` to llama-server) +
      validation (existing file; Strata rejects it) + `lora` in the result
      depends_on: (none)
      refs: R1, R2
- [ ] T2: Pool key `(slug, thinking, lora)` + filenames + render/HTML with label
      (suffix or badge); legacy tolerant
      depends_on: T1
      refs: R2, R3, R4
- [ ] T3: Docs (SPEC/AGENTS/MILLORA: reference to the §6 QLoRA recipe) + real smoke
      with an adapter trained 20 steps (if the conversion tool supports the Qwen3.8
      arch; otherwise document the blockage and close with the verification done) +
      traceability + Completion Gate
      depends_on: T2
      refs: R1, R2, R3, R4, R5
