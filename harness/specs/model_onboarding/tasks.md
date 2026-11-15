# Tasks: model_onboarding

- [ ] T1: `gguf_header.py` — lector de capçalera GGUF stdlib (magic, kv pairs
      general.*, comptatge de tensors `ffn_mtp`/`nextn`, marcador de visió) sobre un
      GGUF sintètic de ~2 KB escrit pel propi test. Tests: magic erròni → error clar,
      kv parsing, detecció MTP, fitxer troncat → missatge, no carrega tensors.
      depends_on: (none)
      refs: R5
- [ ] T2: `hf_client` + `download_verified` — listing del tree API (stub), descàrrega
      amb hash en streaming, mismatch → esborrat + estat `failed`, resume per `Range`
      amb re-verificació final, fitxer sense LFS oid → `unverified` i mai auto-bench.
      Tests: hash ok, hash mismatch, resume truncat, sense oid, rate limit 429 →
      estat explícit.
      depends_on: T1 (només per a la taula final; pot avançar en paral·lel)
      refs: R1, R2, R3, R4, R9
- [ ] T3: `propose_profile` + fact-sheet — draft `.txt` només amb flags segurs
      (`--spec-type` si MTP>0, `--mmproj` si company, `-c` SEMPRE comentat com a TODO
      de probe-context), taula resum amb estat per fitxer. Tests: MTP → flag present,
      sense MTP → flag absent, `-c` mai numèric actiu, company detection, sortida R9.
      depends_on: T1, T2
      refs: R5, R6, R8, R9
- [ ] T4: `--bench` + targeta resum — delegació a `run.main()` des de `_ROOT_DIR`,
      guard de regla d'or GPU, `--yes` salta la confirmació, codis de sortida (0 tot
      bé / 1 res matchejat / 2 ús / 65 entorn). Tests: bench no corre amb fitxer
      no verificat, guard GPU, tabela d'estats final.
      depends_on: T2, T3
      refs: R7, R9
- [ ] T5: docs — Quickstart del README (`ggufbench.fetch --repo …`), entrada a
      `docs/specs.md`. Sense writes a ASSIGNACIO/skills/retired (R8, per construcció).
      depends_on: T4
      refs: R8
