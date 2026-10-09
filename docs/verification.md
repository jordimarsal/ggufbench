# Verification

Aquest document defineix com es demostra que una feina funciona. Cap feature es marca
`done` sense passar la verificació. Sense excepcions.

---

## Verification Levels

### Level 1: Unit Tests (Mandatory)

Tota feature porta tests unitaris (stdlib `unittest`, `tests/test_<modul>.py`). Han de:

- Cobrir tota funció pública nova o modificada, happy path i casos d'error documentats.
- Ser deterministes: dues execucions, mateix resultat (res de xarxa, res de GPU, res de
  temps real).
- Ser ràpids: la suite sencera en menys de 60 s (avui: ~6 s, 124 tests).

```
cd /home/jordi/ia/llama/
python3 -m unittest discover -s benchmark/tests -t .   # última línia: "N tests ... OK"
```

Llegeix el comptador final: una fila de punts sense `F`/`E` no és un resum.

### Level 2: Integration (Mandatory on engine/client changes)

Qualsevol canvi que toqui `client.py`, `server.py` (arrencada, readiness, stop) o el
contracte HTTP ha de tenir test d'integració simulada: el patró de
`tests/test_smoke.py` (arrencada real de servidor + sonda de chat) i els tests de
comanda/venv/log de `tests/test_server.py`. Sense GPU: el smoke e2e salta sol quan no
hi ha models o el port està ocupat.

### Level 3: Smoke del banc real (GPU, opcional)

`python3 -m benchmark.run --engine <engine> --models <nom> --quick` (4 tasques, ~2 min):
smoke manual abans d'una re-mesura llarga. Mai amb els dos motors alhora.

### Level 4: Requirement Traceability (Mandatory for All Features)

Cada requisit R\<n\> del spec mapa a mínim un test que el verifica; el mapa es documenta
a `harness/specs/<feature>/` (vegeu `docs/specs.md`, secció Traceability). Cap feature
es marca `done` amb requisits sense test.

---

## Anti-Patterns

### "Hauria de funcionar" sense tests

Codi correcte per inspecció visual no és codi correcte. Sense test automatitzat, la
feature no està feta. Un bug fix sense el test que l'hauria encertat no està tancat
(precedents que hem de repetir: `ef48e76`, `5a6903b`).

### Tests que només comproven no-throw

Un test sense assert específic sobre el resultat no valida res. Mínim: tipus i una
propietat esperada del valor retornat.

### Barrejar condicions al pool

El pool (`results/models/pool.jsonl`) només és comparable si totes les entrades corren
amb el mateix harness. Canviar tasques, pesos, flags base o afegir dimensions exigeix
**re-mesura** (`--models all`) abans de publicar cap taula. El banner de
`results/report.html` existeix precisament per això.

### Confondre falla del model amb error del servei

Un 500, un timeout o una resposta sense bloc extreuible són EXCLUSIONS (no abaixen el
score, queden a la traça), no falles. Un grader que les compti com a fail està mesurant
el servidor, no el model.

### Marking done without harness/init.sh

Cap feature es marca `done` sense que `harness/init.sh` acabi verd. És la porta final.

### Trusting a subagent's "done" claim

Una resposta de chat no és evidència. Després de cada batch de l'implementador, verifica
a disc: tasques `[x]` a `harness/specs/<name>/tasks.md`, fitxers existents i no buits, i
**corre els gates tu mateix** (`python3 -m unittest discover -s benchmark/tests -t .`).

---

## Security Audit Checklist

Llegeix `"audit_level"` de `harness/feature_list.json` (`basic` → confirma cada ítem
manualment i enregistra la confirmació al review). Aquest projecte **executa codi
generat per LLMs** (dimensions code/agent), així que la superfície és el sandbox:

- [ ] Cap secret, API key o token commitejat (les configs de proveïdors viven fora del repo).
- [ ] Tot `subprocess` passa per `_safe_run` amb timeout; cap execució sense límit.
- [ ] El codi del model només s'executa al sandbox d'`executors.py`: tempdir nou per run,
      `timeout` + `unshare -n` (best-effort), esborrat al final.
- [ ] La sortida del model mai arriba a `eval`/`exec`; l'extrecció de codi és textual
      (`code_extract.py`).
- [ ] L'HTML generat (`html_report.py`) escapa tot el text del pool (`_esc`) i no inclou
      scripts ni recursos externs (test de self-contenció).
- [ ] Els servidors escolten a 127.0.0.1 només; cap exposició de xarxa.
- [ ] Cap `curl | sh` als scripts del projecte (l'única excepció documentada és la
      instal·lació de l'harness mateix, feta una vegada i revisada).

---

## Final Verification

L'últim pas abans de marcar qualsevol feature com a `done`:

```
harness/init.sh
```

Ha d'acabar verd (`[OK]` a l'última línia, inclou la suite de tests). Si falla, la
feature continua `in_progress`. No és opcional.

<!-- harness:module:performance-benchmarks:start -->
## Performance Benchmarks (performance-benchmarks module)

> Appended by the harness `performance-benchmarks` module. Benchmarks are run by
> the reviewer with `bash harness/tools/bench.sh` at `audit_level: strict`. They
> are required when a feature: processes > 1,000 items, involves I/O operations
> (DB, API, file), has concurrency/parallelism concerns, or uses caching or
> memoization.

### Framework per stack

| Stack | Tool | When unavailable |
|---|---|---|
| python | `pytest-benchmark` (mark tests with `@pytest.mark.benchmark`) | `bench.sh` reports record-only |
| typescript / node | `vitest bench` (if configured) | record-only |
| rust | `cargo bench` (if `benches/` configured) | record-only |
| java / android | checklist-only (measure manually if needed) | checklist-only |
| generic | checklist-only | checklist-only |

### Baselines (`harness/baselines.json`)

Starts empty (`{}`). After the first measurement of a function/test, add an entry:

```json
{
  "test_send_email_throughput": {
    "mean_ms": 42.3,
    "thresholds": {
      "mean_ms": { "warning": 1.5, "critical": 2.0 }
    }
  }
}
```

- `mean_ms` is the reference measurement (milliseconds; `mean * 1000` from
  pytest-benchmark).
- Multipliers: exceeding `warning` logs a warning; exceeding `critical` rejects
  approval at `strict`.

### Report (compact — only when benchmarks were required)

```markdown
## Performance Benchmarks
- Scenario: <what was measured>
- Result: <mean/p95 or framework output excerpt>
- vs baseline: ok (<ratio>x) | warning | REGRESSION
```

Without a baseline, `bench.sh` records values and warns; it never blocks.

A transient `harness/.bench-last.json` may be produced by the benchmark run;
delete it before closing the session (it is not user state).

### Nota pròpia del projecte (2026-10-09)

Aquest projecte ÉS un benchmark: el mòdul s'aplica al *rendiment del propi harness* (no
al dels models mesurats). La re-mesura de models (GPU, minuts) no passa per aquí: es
governada pels specs de feature i `docs/MILLORA.md §C7`.
<!-- harness:module:performance-benchmarks:end -->
