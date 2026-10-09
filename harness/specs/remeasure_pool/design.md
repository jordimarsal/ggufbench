# Design: remeasure_pool

Feature d'operació: no hi ha codi nou a produir (el harness ja suporta tot); el disseny
és el **protocol d'execució** i les comprovacions que fan el resultat fiable.

---

## Protocol

1. **Pre-flight (gate d'entrada):**
   - Cap servidor viu: `pgrep -af "llama-server|engine/strata"` buit i ports 8999/8080
     lliures (mai els dos motors alhora — R2).
   - `python3 -m unittest discover` verd abans de cremar GPU.
   - Còpia de seguretat del pool actual a
     `results/models/pool.pre-remeasure.jsonl` (rollback barat si la GPU mor a mig run).
2. **Batch llama (R1, R2):** `python3 -m benchmark.run --models all` des de l'arrel del
   workspace. El harness arrenca/atura `llama-server` per cada model, seqüencialment.
   Progress a stderr → es captura a `harness/logs/remeasure_pool/batch-llama.log`.
3. **Batch Strata (R1, R2):** `python3 -m benchmark.run --engine strata --models
   iq3_xxs` → `harness/logs/remeasure_pool/batch-strata.log`. Només s'arrenca quan el
   batch llama ha acabat i cap procés de llama-server queda viu.
4. **Verificació (R3, R4):** comptar entrades del pool per `ts` (una sola sessió),
   comprovar que cada entrada té `by_level` i `tasks_version: "v2"`, regenerar
   `results/report.html` i verificar que el banner de condicions barrejades NO apareix.
5. **Evidència (R5):** scoreboard final, llistat de ts per model i resultats de les
   comprovacions → `harness/logs/remeasure_pool/summary.log` + taula al Completion Gate.

## Public signatures

(nou codi de producte: cap. Ús del CLI existent.)

## Exceptions and error cases

| Cas | Comportament | Req |
|---|---|---|
| Un model concret no carrega (OOM, GGUF trencat) | `serve_failed`: es registra i es continua amb la resta; el pool conserva la seva entrada antiga marcada com a fallida → es reporta al gate | R1 |
| La GPU es queda sense memòria a mig run | S'atura la run, es restaura `pool.pre-remeasure.jsonl`, es re-planteja (menys models per invocació) | R2 |
| Strata tarda més de 600 s a carregar | El ready-check del harness ja ho cobreix; si falla, es reporta i es reintenta una vegada | R1 |
| Un model deixa entrada amb `by_level` buit | Es detecta a la verificació (pas 4) i es re-executa aquell model sol | R4 |

## Discarded alternatives

1. **Re-mesurar només els models "importants"** — deixaria el pool amb dues condicions i
   el banner permanent: descartat (l'objectiu és un marcador homogeni).
2. **Una sola invocació que mesuri llama i Strata junts** — el CLI és d'un motor per run
   per disseny (mateixa disciplina que mai-els-dos-alhora): descartat.
3. **Esborrar el pool i deixar que el re-run el reconstrueixi** — perd l'històric de
   `results/runs/` i el rollback barat: descartat.
4. **`--quick` per estalviar temps** — mesura 1 tasca per dimensió: no és una re-mesura,
   és un smoke: descartat.
