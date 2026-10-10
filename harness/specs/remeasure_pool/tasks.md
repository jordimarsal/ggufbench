# Tasks: remeasure_pool

- [x] T1: Pre-flight — sense servidors vius (ports 8999/8080 lliures), suite unittest
      verda, backup del pool a `results/models/pool.pre-remeasure.jsonl`
      depends_on: (none)
      refs: R2

- [x] T2: Batch llama — `python3 -m benchmark.run --models all` + ON (doble batch thinking_batches: off 10/10 + on 10/10, amb restart documentat al log per mort prematura del procés) (seqüencial, un servidor
      cada vegada) amb log a `harness/logs/remeasure_pool/batch-llama.log`
      depends_on: T1
      refs: R1, R2

- [x] T3: Batch Strata — `python3 -m benchmark.run --engine strata --models iq3_xxs` + ON (strata on/v3 code=0.92, exit 0, batch-strata-on.log)
      amb log a `harness/logs/remeasure_pool/batch-strata.log` (només quan cap
      llama-server quedi viu)
      depends_on: T2
      refs: R1, R2

- [x] T4: Verificació — pool amb entrades d'una sola sessió i amb by_level +
      tasks_version v2; regenerar `results/report.html` i comprovar que el banner de
      condicions barrejades no apareix
      depends_on: T3
      refs: R3, R4

- [x] T5: Evidència i gate — scoreboard final, ts per model i comprovacions a
      `harness/logs/remeasure_pool/summary.log`; traçabilitat; demanar Completion Gate
      depends_on: T4
      refs: R5
