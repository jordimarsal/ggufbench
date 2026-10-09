# Arquitectura

Aquest document defineix els estàndards arquitectònics del projecte: els principis que
guien tota decisió de disseny, els fluxos de dades i les fronteres que no es poden
creuar. Disseny complet: `docs/SPEC.md` · pla de millora: `docs/MILLORA.md`.

---

## Principis

1. **Mateixes condicions per a tots els models.** El valor del banc és la
   comparabilitat: flags base comuns (`config.SERVER_FLAGS` + `CACHE_FLAGS`), perfil per
   model (`models/<model>.txt`, aplicat al final), temp/seed fixos, mateixos prompts.
2. **Honestitat del resultat.** Una tasca pot FALLAR (el model no ha sabut) o quedar
   EXCLOSA (error transient del servidor/xarxa, codi no extreuible). Mai es confonen:
   les exclusions no abaixen el score però queden enregistrades a la traça.
3. **Zero dependències.** stdlib Python 3.12. La suite sencera ha de córrer en un runner
   buit i sense GPU en menys de 60 s. Això és una característica, no una limitació.
4. **Data-as-code.** Una tasca = un fitxer Python amb constants (`ID`, `PROMPT`,
   `TEST_CODE`, `EXPECTED`...). Sense registre, sense JSON: es deixa un fitxer i ja està.
5. **Reproduïbilitat.** Cada resultat porta `ts`, `tasks_version`, `server_build`,
   `engine` i `model_config_flags`: qualsevol fila del marcador es pot explicar.
6. **Dos motors, mai alhora.** llama-server (port 8999) i Strata (port 8080) competeixen
   per les mateixes GPU. El harness arrenca el servidor que cal i l'atura amb el grup de
   processos sencer (`start_new_session` + `killpg`).

---

## Data Flow

```
tasks/<dim>/**.py ──tasks_loader──▶ run._bench_one
                                      │  server.ServerManager (arrenca llama | strata)
                                      │  client.chat  ──▶ /v1/chat/completions
                                      ▼
                                   graders (speed · tools · code · agent)
                                      │  executors: sandbox (tempdir nou, timeout, unshare -n)
                                      ▼
                                   report (upsert results/models/pool.jsonl
                                           + històric results/runs/<ts>-<slug>.json)
                                      ▼
                        CLI (taules) · html_report (results/report.html)
```

Calibració: les tasques de codi amb resposta sense bloc extreuible s'escalen per
`CODE_LADDER` i el pressupost que funciona es persisteix a `results/token_budgets.json`.

---

## Do Not

- **No introduir dependències externes** (ni pytest, ni requests): la promesa és
  "checkout net + python3" i el CI ho aprofita.
- **No canviar tasques, pesos ni flags base sense re-mesura del pool** (upsert per slug:
  una fila amb condicions velles al costat de condicions noves és una mentida).
- **No llençar mai una run de llama i una de Strata concurrentment.**
- **No confiar en la sortida del model:** només els graders (execució real en sandbox)
  decideixen el score; una resposta bonica sense tests no és un pass.
- **El port/host/model els fixa el harness** (`server._INFRA_FLAGS`): el `.txt` d'un
  model no els pot canviar (un port diferent trencaria el ready-check).
- **Cap bug fix sense el test que l'hauria encertat** (precedents: `ef48e76`,
  `5a6903b` — dues tasques impossibles i un agent java trencat que cap model havia
  passat mai).
