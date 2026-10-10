# Tasks: thinking_batches

- [x] T1: CLI `--thinking on|off` (default off) + kwarg al cos + `thinking` al resultat;
      els prompts/dims no canvien amb el mode (test de cossos idèntics on/off)
      depends_on: (none)
      refs: R1, R6

- [x] T2: Clau de pool `(slug, thinking)` (save/load/forget + filenames de runs) +
      render tolerant de legacy (marca `—`); `slug` intacte
      depends_on: T1
      refs: R2

- [x] T3: `token_budget` clavat per `(model, thinking)` + `_schema = 2` (era 16384
      ignorada i regenerada)
      depends_on: T2
      refs: R2

- [x] T4: `CODE_MAX_TOKENS = 32768` + cap de rellotge 1000 (mateixa fórmula);
      actualitzar COS (no noms) dels tests de_timeout_scaling afectats
      depends_on: T3
      refs: R3

- [x] T5: Report: columna `THINK` + ` (N excl.)` a Taula 1, marca de mode a Taula 3,
      banner intacte (test del banner existent verd)
      depends_on: T2
      refs: R4, R5

- [x] T6: HTML: badge de mode + línia `excloses: N/M` a la targeta; matriu intacta
      depends_on: T5
      refs: R4, R5

- [x] T7: Docs (SPEC: `--thinking`, pressupost 32768, columna THINK; AGENTS.md;
      MILLORA: tancar D6 com a superat per aquesta feature) + traçabilitat +
      harness/init.sh + demanar Completion Gate
      depends_on: T4, T6
      refs: R1, R2, R3, R4, R5, R6, R7
