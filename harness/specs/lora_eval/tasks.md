# Tasks: lora_eval

- [ ] T1: `--lora` CLI + perfil `.txt` → `build_args` (`--lora` a llama-server) +
      validació (fitxer existent; Strata ho rebutja) + `lora` al resultat
      depends_on: (none)
      refs: R1, R2
- [ ] T2: Clau de pool `(slug, thinking, lora)` + filenames + render/HTML amb etiqueta
      (sufix o badge); legacy tolerant
      depends_on: T1
      refs: R2, R3, R4
- [ ] T3: Docs (SPEC/AGENTS/MILLORA: referència a la receta QLoRA de §6) + smoke real
      amb un adaptador entrenat 20 steps (si l'eina de conversió suporta l'arch
      Qwen3.8; si no, documentar el bloqueig i tancar amb la verificació feta) +
      traçabilitat + Completion Gate
      depends_on: T2
      refs: R1, R2, R3, R4, R5
