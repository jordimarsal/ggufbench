# Model Benchmark — Document de disseny

**Data:** 2026-08-03
**Ubicació:** `/home/jordi/ia/llama/benchmark/`
**Estat:** Disseny aprovat (pendent de pla d'implementació)

## 1. Objectiu

Benchmark automàtic per comparar models locals (servits per `llama-server`) sota
**les mateixes condicions**, amb un marcador que puntuï 4 dimensions:

1. **Velocitat** — rendiment brut.
2. **Tool-calling** — fiabilitat produint crides d'eina estructurades.
3. **Codi amb tests** — correcció implementant/arreglant codi (4 idiomes).
4. **Agent multi-pas** — capacitat de llegir → entendre → editar → verificar.

L'objectiu final és triar el millor model per a **opencode** (agent programador).

## 2. Principi: "mateixes condicions"

- **Flags fixos** per tots els models (extrets de `start-dev-ai.sh`):
  `temp 0.2`, `top-p 0.95`, `seed 42`, `repeat-penalty 1.1`, `-ngl 999`,
  `--flash-attn auto`, `--no-mmap`, `--jinja`, cache KV `q4_0/q4_0`, `--parallel 1`.
- **Context (`-c`)**: dos modes via flag `--context`:
  - `fixed` (default): `16384` per tots → KV igual → velocitats comparables.
  - `adapted`: el context viable de cada model (llògica de `start-dev-ai.sh`).
- `--tensor-split` sí adapta (multi-GPU, proporció de VRAM lliura).
- **Warmup** de 1 generació abans de mesurar/qualsevol tasca.
- Mateixos prompts/tests per tots els models.

## 3. Arquitectura

```
benchmark/
├── run.py            # CLI / entry point
├── config.py         # pesos, defaults, paths, flags del servidor
├── server.py         # cicle de vida de llama-server (start/stop/ready)
├── client.py         # client HTTP cap a /v1/chat/completions
├── executors.py      # runners per llenguatge (py/bash/java/ts) + sandbox
├── graders.py        # puntuació per dimensió
├── agent.py          # loop d'agent multi-pas + entorn mock
├── report.py         # marcador (taula terminal + JSON)
├── tasks/
│   ├── speed/
│   ├── tools/
│   ├── code/{python,bash,java,typescript}/
│   └── agent/{python,bash,java,typescript}/
├── results/
│   ├── models/        # <slug>.json — resultat més recent per model (el POOL)
│   └── runs/          # <ts>-<slug>.json — històric append-only de cada execució
└── docs/SPEC.md
```

### Flux principal (run.py)
```
si --scoreboard:                      # mode només-lectura
    report(results/models/*.json)     # mostra taules acumulades i surt

models = resolve_models(args)
per cada model:
    server.start(model)            # arrenca amb flags de config.py
    wait_ready()                   # inferència real (no /v1/models)
    warmup()
    result = {}
    per cada dimensió habilitada:
        result[dim] = run_dimension(dim, model)   # corre tasques + classifica
    server.stop()
    save result/models/<slug>.json      # actualitza el pool (sobreescriu)
    save result/runs/<ts>-<slug>.json   # històric append-only
report(results/models/*.json)           # scoreboard ACUMULAT de tots els models
```

## 4. Components

### 4.1 server.py — gestor de llama-server
- `start(model)`: arranca `llama-server` (subprocess) amb els flags de
  `config.py` + `-c` (segons mode) + `--tensor-split` (segons VRAM).
- `wait_ready()`: polling fins que un chat de prova retorna `"choices"`
  (no només `/v1/models`, que respon abans d'estar llest per inferència).
- `stop()`: SIGKILL + espera.
- Un sol model alhora (port fixe, ex. 8999).

### 4.2 client.py — client HTTP
- `chat(messages, tools=None, max_tokens=..., temperature=...)` → dict.
- Captura `timings` (gen_tps, prompt_tps, predicted_ms) per a velocitat.
- Timeout configurable (default 60s).
- Llegible pel loop d'agent (suporta multi-turn).

### 4.3 executors.py — execució multi-llenguatge + sandbox
Un executor per idioma. Tots comparteixen la mateixa interfície:
`run(lang, solution_code, test_code) -> (passed: bool, output: str)`.

| Lang | Solution | Test (grader) | Comanda |
|---|---|---|---|
| python | `solution.py` | `test.py` (import + asserts) | `python3 test.py` |
| bash | `solution.sh` (funcions) | `test.sh` (source + asserts) | `bash test.sh` |
| java | `Solution.java` (classe+mètode) | `Test.java` (main + asserts) | `javac *.java && java Test` |
| typescript | `solution.ts` | `test.ts` (import + asserts) | `bun test.ts` |

**Extracció de codi**: de la resposta del model, es pren el primer bloc
` ```lang ... ``` ` corresponent al llenguatge de la tasca. Si no n'hi ha → fail.

**Sandbox** (per cada execució):
- tempdir nou i exclusiu.
- `timeout 30s` (matat el procés si excedeix).
- xarxa bloquejada: `unshare -n` si disponible; sinó `env -i` + sense `PATH` de xarxa.
- `ulimit` (CPU/memòria).
- Mai s'executa fora del tempdir.

Toolchains verificats al sistema: Python 3.12, Bash 5.2, Java 22 (jdk+javac),
Bun 1.3.9 (per TS). Sense pytest → els tests Python fan servir `assert` nus.

### 4.4 graders.py — classificació per dimensió

**speed**: 1 tasca. Pren `timings.predicted_per_second` (o càlcul
`predicted_n / (predicted_ms/1000)`). 3 mostres, mediana. Mètriques:
`gen_tps`, `prompt_tps`, `ttft_ms`.

**tools**: per cada tasca, `{prompt, tools, expected}`. Classificació:
- `pass` si `message.tool_calls[0].function.name == expected.name` **i**
  `arguments` (parsejat com JSON) == `expected.arguments`.
- Cas "no-op": `pass` si **no** hi ha `tool_calls` (no ha d'inventar).

**code**: per cada tasca `{lang, prompt, test_code}`. Extrou codi → executor →
`pass` si exit 0.

**agent**: delega a `agent.py` (4.5).

Puntuació per dimensió = `passats / total` (0..1). Velocitat = normalitzada
respecte el millor tps del conjunt (el més ràpid → 1.0).

**Agregació per llenguatge**: les dimensions `code` i `agent` calculen, a més
del score global de la dimensió, `by_lang` = score per cada idioma present
(`python|bash|java|typescript`). Les dimensions `tools` i `speed` no són per
llenguatge (són lang-agnostic). El `report.py` fa servir aquest `by_lang` per
la Taula 2 i el perfil per llenguatge.

### 4.5 agent.py — loop d'agent multi-pas
Mini-entorn de codi en memòria. Una tasca agent defineix:
`{lang, goal, initial_files, max_turns}`.

Eines disponibles per al model: `read_file(path)`, `write_file(path, content)`,
`run_tests()`. El loop:
```
env = dict(initial_files)
history = [user(goal)]
per torn en 1..max_turns:
    resp = client.chat(history, tools=[read_file, write_file, run_tests])
    si no hi ha tool_calls: break
    per cada tool_call:
        result = execute_tool(tool_call, env, lang)   # muta env / corre tests
        history.append(tool(result))
success = check_goal(env, lang)   # run_tests final passa?
```
`run_tests()` usa `executors.py` amb el llenguatge de la tasca: escriu els
fitxers actualials de `env` al tempdir, corre el test, retorna pass/fail + output.
`check_goal` = `run_tests()` final amb exit 0.

### 4.6 report.py — marcador i detall
El reporting té **3 nivells de granularitat**:

**Taula 1 — Global** (sempre, ordenada per puntuació global):
```
MODEL                          gen_tps   tools   code   agent   GLOBAL
qwen3-vl-8b                      97.7    88%     75%    67%     0.76
qwen3-14b                        48.0    100%    88%    83%     0.91
```

**Taula 2 — Per llenguatge** (sempre; code i agent desglossats):
```
MODEL                          code:py bas java ts    agent:py bas java ts
qwen3-14b                          100% 100%  50% 100%        100%  —  50% 100%
qwen3-vl-8b                        100%  50%   0% 100%         50%  —   0% 100%
```
Cel·la `—` = sense tasques d'aquell idioma per aquella dimensió.

**Taula 3 — Detall per tasca** (amb `--verbose` / `-v`):
```
MODEL            DIM     LANG   TASK              PASS   DETALL
qwen3-14b        tools   —      multi-arg         ✓      get_weather(city=Paris)
qwen3-14b        code    java   implementa-stack  ✗      AssertionError line 12
qwen3-14b        agent   py     fix-bug-fib       ✓      tests pass (2/2)
qwen3-vl-8b      code    java   implementa-stack  ✗      no code block found
...
```

**JSON + emmagatzematge incremental** — les taules creixen model a model sense
re-executar els altres. Dues capes:
- `results/models/<slug>.json` → **resultat més recent per model** (pool actual,
  sobreescriu al re-executar aquell model). `<slug>` = nom del model sanejat.
- `results/runs/<timestamp>-<slug>.json` → **històric** append-only (auditoria,
  poder comparar runs posteriors).

Cada resultat porta metadata de condicions per poder barregar runs de forma
justa: `context_mode`, `tasks_version` (hash de la suite), `weights`, `ts`,
`server_build` (versió de llama.cpp). El scoreboard avisa (o filtra) si es
barregen resultats amb condicions diferents.

El JSON per model és:
```json
{
  "model": "qwen3-14b",
  "ts": "2026-08-03T20:30:00",
  "context_mode": "fixed",
  "tasks_version": "a1b2c3",
  "server_build": "10250",
  "global": 0.91,
  "speed": {"gen_tps": 48.0, "prompt_tps": 2600.0, "ttft_ms": 220},
  "tools": {"score": 1.0, "tasks": [
    {"name":"multi-arg","pass":true,"got":{"name":"get_weather","arguments":{"city":"Paris"}},"expected":{...}},
    ...]},
  "code": {
    "score": 0.88,
    "by_lang": {"python":1.0, "bash":1.0, "java":0.5, "typescript":1.0},
    "tasks": [{"name":"stack","lang":"java","pass":false,"output":"AssertionError...","elapsed_ms":1240}, ...]
  },
  "agent": {
    "score": 0.83,
    "by_lang": {"python":1.0, "typescript":1.0, "java":0.5, "bash":null},
    "tasks": [{"name":"fix-fib","lang":"python","pass":true,"turns":3,"tool_calls":4,"final_tests":"pass"}, ...]
  }
}
```
Runs anteriors es preserven (històric). Suport `--compare <ts1> <ts2>` (futur).

**Scoreboard acumulat**: la normalització de velocitat (millor tps → 1.0) i els
% es recalculen en mostrar, sobre el pool de models carregat (no es guarda
normalitzat) — així afegir un model més ràpid reescala la resta de forma justa.

**Perfil per llenguatge** (resum ràpid): el report extreu, per cada model, els
idiomes on supera el llindar (ex. ≥75%) i els que no — per respondre directament
"en quins llenguatges m'és fiable aquest model".

## 5. Puntuació global

Suma ponderada (a `config.py`, configurable):
- Tools: **0.30**
- Codi: **0.30**
- Agent: **0.25**
- Velocitat: **0.15**

Velocitat normalitzada (millor tps → 1.0) perquè el raw t/s no domini.

## 6. Suite de tasques (~23)

| Dimensió | # | Detall |
|---|---:|---|
| speed | 1 | prompt fix, lang-agnostic |
| tools | 8 | 1-arg, multi-arg, tria-eina, no-op, args-erronis, encadenament, dependències, refactor |
| code | 8 | 2 per idioma (bash, python, java, typescript): implementa-funció + arregla-bug |
| agent | 6 | python×2, typescript×2, java×1, bash×1 |

Format de cada tasca: fitxer Python amb constants descriptives
(`PROMPT`, `LANG`, `TEST_CODE`, `EXPECTED`, etc.) — test code com a string.
Una tasca = un fitxer, autònoma i descrivible.

## 7. CLI

```
benchmark/run.py [opcions]
  --models all|<llista>        # default: all (models/*.gguf)
  --context fixed|adapted      # default: fixed (16384)
  --dims speed,tools,code,agent  # subset; default: totes
  --lang python,java,...       # filtra tasques de codi/agent per idioma
  --quick                      # 1 tasca per dimensió (smoke test del harness)
  -v, --verbose                # mostra la Taula 3 (detall per tasca)
  --scoreboard                 # NOMÉS mostra les taules acumulades (sense executar res)
  --forget <model>             # esborra un model del pool
  --json                       # només escup el JSON final (per scripts)
  --port N                     # default 8999
  --weights tools=0.3,code=0.3,agent=0.25,speed=0.15
```
**Workflow incremental**:
- `run.py --models qwen3-vl` → executa i guarda; mostra scoreboard amb tots els
  models del pool (inicialment només aquest).
- `run.py --models qwen3-14b` → afegeix al pool; scoreboard amb tots dos.
- `run.py --scoreboard` → re-imprimeix les taules sense re-executar res.
- `run.py --models qwen3-vl` (un altre dia) → re-executa i **actualitza** aquell
  model (sobreescriu); la resta es manté.

## 8. Tractament d'errors

- Model no carrega (OOM, crash) → es marca `serve_failed`, es salta, es continua.
- Tasca amb error/timeout → es registra `error`, **no** tomba tota la run.
- Server penjat → `stop()` fort + continua amb el següent.

## 9. Fora d'abast (v2+)

- **Enfocament C** (mini-opencode real end-to-end amb un agent de veritat).
- Integració directa amb opencode (CLI) per tests de mundo real.
- Suport multimodal (imatges).
- Comparació visual entre runs (`--compare` amb HTML).
- Sandbox amb firejail/bwrap (ara: tempdir+timeout+unshare).

## 10. Decisions pendents

Cap — totes les decisions clau estan resoltes:
- Llenguatges: bash, python, java, typescript (confirmat).
- Tasques: ~23, extens (confirmat).
- Context: ambdós modes via flag (confirmat).
- Orquestració: automàtica (confirmat).
