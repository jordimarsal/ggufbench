# Design: thinking_batches

## Fitxers a modificar (paquet pla, sense `src/`)

| Fitxer | Canvi |
|---|---|
| `run.py` | Flag `--thinking on\|off` (default `off`); el passa a `ServerManager`, al cos del chat (kwarg) i al `result["thinking"]`. El protocol (dims/langs/levels) no el toca. |
| `config.py` | `THINKING_DEFAULT = "off"`; generalitzar `STRATA_EXTRA_BODY` a constructor de cos per mode: `thinking_body(engine, mode)` → `{"chat_template_kwargs": {"enable_thinking": False}}` quan `off`, `{}` quan `on` (mateix canal pels dos motors). |
| `server.py` | `ServerManager.__init__` accepta `thinking` (només per registrar a `describe_*`/metadades; el control efectiu va pel cos, no per flags — així cap `.txt` de model el pot sobreescriure). |
| `report.py` | Upsert/load per `(slug, thinking)`; `_forget_matches` intacte (esborra els dos modes); Taula 1: columna `THINK` (`on`/`off`/`—` legacy) + cel·la code amb ` (N excl.)`; Taules 2/3: files separades ja existents (una per entrada) + columna/marca de mode a la 3. Banner intacte. |
| `html_report.py` | Badge de mode per fila + línia `excloses: N/M` a la targeta; matriu i ordenació intactes. |
| `token_budget.py` | Clau `_key(dim, slug, thinking, lang, task_id)` + `_schema = 2` al fitxer: sense `_schema` (era 16384) les entrades s'ignoren i es sobreescriuen al pròxim run. |
| `graders.py` | `CODE_MAX_TOKENS = 32768`, `CODE_LADDER = [32768]`; `code_timeout`: mateixa fórmula, sostre `600 → 1000` (cobreix 32768 a 44 t/s: `60 + 32768/44×1.25 = 991 ≤ 1000`; els ràpids no canvien, el cap només talla penjades). |

## Signatures noves

```python
# config.py
THINKING_DEFAULT = "off"
def thinking_body(engine: str, mode: str) -> dict: ...  # {} si on

# run.py
ap.add_argument("--thinking", choices=["on", "off"], default=config.THINKING_DEFAULT)

# token_budget.py
_SCHEMA = 2
def _key(dim, model_slug, thinking, lang, task_id) -> str: ...
```

`result["thinking"]` sempre present en resultats nous (`"on"`/`"off"`). Slug
(`config.slug`) intacte: la identitat del model no canvia, només la clau d'upsert.

## Casos d'error

- `--thinking bogus` → `argparse` mor (mateix patró que `--level`).
- Pool amb files legacy (sense `thinking`): render `—`, upsert les conserva fins que la
  re-mesura les substitueix (clau `(slug, None)` no col·lisiona amb `(slug, off)`).
- `token_budgets.json` sense `_schema` → s'ignora sencer (era 16384) i es regenera.
- Think batch amb pressupostos petits (speed/tools 128/256): els pensadors exclouran
  en massa — dada registrada (R6), no error.

## Alternativa descartada

**Interruptor per model (només híbrids en think-batch).** Estalvia GPU però trenca el
principi nº 1 (mateix protocol per a tothom) i introdueix una llista de capacitats
per model que caldria mantenir. El cost (~2× GPU, ja acceptat) compra comparabilitat;
en models sense think el segon batch és un no-op que ho confirma.

## Tests (noms d'IDs existents que NO es poden reanomenar)

`test_formula_floors_ceils_and_falls_back`, `test_scaled_timeout_applied_to_the_single_attempt`,
`test_transient_timeout_still_excludes` (timeout_scaling) i `test_banner_only_with_mixed_dates`
canvien de COS (nou cap, nou key) però conserven el NOM: `--all` ha de seguir verd.

## Architectural Decisions

### ADR-1: doble batch uniforme en comptes de toggle per model
**Context:** cal mesurar think/no-think sense trencar la comparabilitat.
**Decision:** els dos batchs corren per a tots els models amb el mateix protocol.
**Alternatives considered:** think-batch només per a híbrids (descartada: vegeu a dalt).
**Consequences:** ~2× temps de GPU; els no-pensadors donen files quasi idèntiques (control).

### ADR-2: clau de pool `(slug, thinking)`, no dos pools
**Context:** l'upsert per slug solaparia els batchs.
**Decision:** una sola taula amb columna `THINK`; el lector compara like-for-like.
**Alternatives considered:** dos `pool-think.jsonl` / `pool-nothink.jsonl` (descartada:
duplica scoreboard/HTML/forget i el banner hauria de raonar entre fitxers).
**Consequences:** `load_pool`/`save_result`/`forget` canvien de clau; el slug de
visualització no canvia.

### ADR-3: 32768 en un sol intent, no re-escala
**Context:** decisió del revisor (Q1 inicia a 32768).
**Decision:** `CODE_LADDER = [32768]`; res de segon esglaó condicional.
**Alternatives considered:** 16384 + reintent a 32768 si sostre (descartada: amb
seed/temp fixos el prefix és determinista — històric feature 4 — i el reintent
afegeix peticions mortes; si el sostre era pensament, més tokens no garanteixen
resposta).
**Consequences:** cada tasca de code paga el pitjor cas una vegada; el cap de rellotge
puja a 1000.

### ADR-4: control del think pel cos, no per flags de servidor
**Context:** dues vies possibles (`--reasoning off` vs `chat_template_kwargs`).
**Decision:** kwarg al cos pels dos motors.
**Alternatives considered:** flag `--reasoning off` al `ServerManager` (descartada: els
`.txt` de model s'apliquen AL FINAL i podrien sobreescriure'l; el cos no té aquest
canal de sobreescriptura).
**Consequences:** `ServerManager` només registra el mode; el comportament el fixa la
petició.
