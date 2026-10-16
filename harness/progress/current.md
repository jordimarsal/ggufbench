# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 6 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_
- **Agent:** _—_

## Plan

_The task set is frozen at v5 (tools 18 · code 72 · agent 72) and the sampler is pinned in the
baseline (`ed3153c0`), so what is left is a night of GPU: the holes on the board are
conditions, not data. Sequence fixed with the human (2026-10-14), running detached:_

1. **Dense fleet, thinking OFF, at v5** — Heretic, TurboFCFusion, UD-Q3_K_XL, Qwen3-VL-8B,
   `--runs 3`. Running; log `harness/logs/v5_off/dense.log`. Upserts the four dense rows.
2. **Strata: calibrate the engine, then OFF, then ON.** `./setup.sh --calibrate` measures the
   four PC-dependent settings (the share of missed experts copied over PCIe instead of computed
   by the CPU, the draft confidence, the CPU pool threads, the VRAM expert cache) and writes
   them **into the config's args** — so they land in `model_config_flags` of every row measured
   after it (the §C9 lesson: a condition that differs must be visible in the row). Calibrate
   both configs (`iq3_xxs`, `swift-iq3_xxs`), then OFF ×3 on both and ON ×3 on `iq3_xxs` (the
   ★ optimal-mode marker needs the pair; the swift row has no ON counterpart in the pool).
3. **Fleet ON at v5** — 8 GGUF (3 MoE + MiniCPM + the 4 dense) with `--thinking on` and the
   per-call caps raised **for the whole batch**, the same value in every row: `--tools-max-tokens
   256 --agent-max-tokens 1024`. The 128-token cap is measurably too tight (Heretic's OFF run
   hit it twice on `refuse_delete_protected`). The code budget stays 32768 so the ON/OFF pair
   is not confounded by anything but the mode.
4. **Then the paperwork**: `--scoreboard --html` + `harness/tools/publish-report.sh`, the three
   write-ups (`docs/writeups/*.md`) and the README tables, which still describe the C1-era
   condition (12/60/28, "42 multi-step agent tasks").

## Log

- **2026-10-14 · New model preview: MiniCPM-V 4.7 35B-A3B (OpenBMB, human order).** The tweet
  (2026-10-12) announces the MiniCPM-V 4.7 series; the 35B-A3B is the first MoE of the family
  (on-device MLLM, LES lookahead expert scheduling, Apache-2.0). Checked before downloading:
  the GGUF declares arch **`qwen35moe`**, which this repo's llama.cpp (0.6.0-dev+4413a1924)
  supports — `llama_model_qwen35moe` + `src/models/qwen35moe.cpp` are in libllama.so, MTP
  branch included. Header read over HTTP range (no download): ctx 262144, 40 blocks with
  `full_attention_interval 4` (hybrid SSM/attention), GQA 2/16 with key/value length 256 →
  KV is cheap (~1.5 GB at 128k, q8_0), 256 experts / 8 active, **no MTP tensors** (their
  speculative path is the separate DSpark draft + LES fork), and the chat template honours
  `enable_thinking: false` → the harness's OFF mode is a clean instruct run.
  Downloaded `MiniCPM-V-4_7-35B-A3B-Q4_K_M.gguf` (21.2 GB) with `hf download` into
  `models/`, plus the profile `models/MiniCPM-V-4_7-35B-A3B-Q4_K_M.txt` (`-c 131072`: the
  32768 code budget must fit with the prompt; sampling stays the harness baseline).
  Run: `--models models/MiniCPM-V-4_7-35B-A3B-Q4_K_M.gguf --runs 3` (thinking OFF, the pool
  protocol), log in `harness/logs/minicpm_v47/`.
- **2026-10-14 · First run done (24 min) — and it found a grader bug, not a model trait.** The
  row came out `tools 1.000 ±0 · code 0.571 ±4 · agent 0.895 ±1 · 18→23 ms · global 0.826 ±1`
  with a nonsense level breakdown (`easy 0.44 < hard 0.75`) and a bash-only language pattern.
  Reading the trace showed java/python/typescript tasks recorded as `bash` entries: the
  multi-run aggregation looked entries up by `id`, and ids are unique per *dimension*, not per
  language (the easy tier mirrors `bubble_sort` etc. across the four) — so every shared id took
  bash's outcome. The same refactor had also hardcoded `grade_agent`'s `by_lang` to `{}` and
  dropped `lang` from the agent trace. Fixed (MILLORA §D10, commit 53779ba) with 5 regression
  tests; SPEC §4.4 + AGENTS §3 now state the identity rule. **Consequence: every existing row's
  code/agent score is skewed — the C9 re-measure is the only way to valid numbers**, and the
  MiniCPM row was re-measured right after the fix (log `batch-off-runs3-fixed.log`).
  Tweets aside, the interesting part: the model itself looks strong on tools/agent and weak on
  bash (it answers bash prompts with rust/python fences → exclusions), which the fixed grader
  will now attribute to the right language.
- **2026-10-14 · Sampler settled with data, not doctrine (baseline `f982b06a` → `ed3153c0`).**
  The Ornith A/B: A (temp 0.2 / top_k 40, the harness baseline) against B (temp 1.0 / top_k 20,
  the author's card) gave **0 of 72** code verdict flips with identical code tokens (16,433) and
  2 of 72 agent flips (0.928 → 0.918, inside the ±). So the sampler stays pinned in the baseline
  and (B) remains available as an explicit per-profile option. Receipts: the two
  `results/runs/20261014-*ornith*-off.json` files. Rows measured before the pin keep the old id
  and the board flags them — the reason the dense/MoE OFF rows are re-measured tonight.
- **2026-10-14 · LFM2.5-24B-A2B retired (human decision) — and the reason is a harness lesson.**
  Its chat template always opens a `<think>` block and has no `enable_thinking` switch, so the
  harness's OFF mode was impossible for it and the reasoning ate the per-call budget: 0.59 global
  (tools 78 / code 74 / agent 51). A focused re-run with 256/2048-token caps lifted tools to ~91%
  and the agent to ~75% at half of the dimension — better, still under the fleet's 87-93%. The
  GGUF and its profile are deleted; the stem is in `harness/retired.json` so its pool row stays as
  a record and renders gray (`7a73168`).
- **2026-10-14 · Probes and traceability, so that no condition can hide.** Every row now carries
  `code_budget` / `code_budget_stored` and `ctx_resolved` + `ctx_source`, and the harness probes
  the run itself (`code_budget_hits`, `tools_capped`, `agent_empty_replies`,
  `thinking_mode_applied` via `/props`, with a `probes:` line on the model card). Live proof
  today: the LFM pass warned on 7 truncated tool calls and 5 empty agent turns, and Heretic's OFF
  run warned twice on the 128-token tool cap — which is the evidence behind the 256/1024 caps of
  the ON batch. Legacy `token_budgets.json` entries (37 rows, 4096/8192) are inert: no `_schema: 2`.
- **2026-10-14 · Strata was calibrated — with the engine of 2026-10-01.** Checked
  `~/.config/strata/settings.json`: the calibration ran on 2026-10-01 for
  `qwen3.8-flash-next-iq3_xxs|131072` and kept a single setting, `--pool-workers 4` (65.5 t/s
  then), which is the value our config carries. That day's engine is not today's (0.1.44.1), so
  the measurement is re-run as the first Strata step of the night. `--calibrate` rewrites only the
  config's args and the settings file — it never reinstalls — and `--yes --no-start` makes it
  non-interactive without leaving a server up.

## 2026-10-16 · Heretic: l'A/B d'MTP (i dos paranys pel camí)

**El MTP natiu no existeix en aquest GGUF.** Verificat amb el lector de GGUF: l'Heretic no té cap
bloc MTP (no hi ha `blk.64.nextn.*`; l'últim és `blk.63`) i el servidor ho diu tal qual: "context
type MTP requested but model doesn't contain MTP layers". La nota que hi havia al perfil ("el GGUF
el declara (ffn_mtp)") era meva i era falsa, i està corregida. Qui sí que en porta: qwen36
(`blk.40`), Ornith-APEX (`blk.40`) i UD-Q3 (`blk.64`).

**La família, però, porta el cap MTP separat**: `models/nerkior/mtp-Qwen3.8-27B-Q4_0.gguf` (18
tensors: `blk.64.nextn.*` + `token_embd` + `output`), i el build l'accepta com a esborrany
(`--spec-draft-model`). Sonda en viu a `-c 86016` amb el cap a la GPU: **151,4 t/s contra 47,0
t/s** del mateix model sol, 149/197 acceptats (76%). Amb el cap a CPU: 10,9 t/s — pèrdua.

**Disseny del 2×2**: quatre cames a `-c 86016` (el pin del seu OFF, on el cap hi cap; a 233472 no
hi entra: el KV de l'esborrany demana 456 MiB i el seu graf 1220 MiB a la targeta 0), OFF/ON ×
sense/amb cap, 3 passades, sostres 1024/8192, perfil tornat a 233472 al final i **taulell
protegit** (`pool.before-heretic-mtp-ab.jsonl` + restauració per `trap`): les files de l'A/B
viuen com a rebuts a `results/runs/` i no toquen el taulell. Les cames amb cap diuen "amb cap de
la família", no "MTP natiu" — mesuren el cap com a esborrany, que és una altra cosa.

**Dos paranys, tots dos del mateix tipus** (una condició que diu una cosa i n'és una altra):

1. *La llista blanca del harness* (`config.py`) portava el nom vell de la bandera (`-md`) i
   tirava la nova (`--spec-draft-model`) sense aturar la passada: la cama va sortir amb
   `--spec-type draft-mtp` i sense cap, i el servidor va morir en carregar. Arreglat (`b1efb8e`)
   amb test que el nomena, mateix tractament que les banderes de mostreig de §C11. La sonda en
   viu no hi va caure perquè afegia les banderes *després* de `build_args`.
2. *El meu esborrador del perfil* ancorava els patrons en el nom solt i deixava
   `--spec-draft-model <ruta>` i `--spec-draft-n-max 4` al fitxer després de cada neteja: per
   això la cama 3, tot i ser un ON net, arrossega un `--spec-draft-n-max 4` inert (sense
   `--spec-type` no hi ha esborrany). Esborrador arreglat; queda anotat com a condició que hi és.

**Estat de les cames** — tancat el 16-10 a les 17:15, amb perfil (233472, sense cap) i taulell
(byte a byte igual al snapshot) restaurats. Totes a `-c 86016`, 3 passades, sostres 1024/8192:

| cama | mode | cap | tools | code | agent | sonda | t/s | global | passada |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OFF sense cap | no | 100 | 86,1 | 93,1 | 69 ms | 57,6 | 0,819 | 56 min |
| 2 | OFF amb cap | sí | 100 | 82,9 | 94,9 | 41 ms | 97,2 | 0,833 | 33 min |
| 3 | ON sense cap | no | 94,4 | 89,8 | 97,2 | 1075 ms | 66,9 | 0,798 | 7 h 44 |

**Què en surt**: el cap funciona i és un guany d'**1,7×** (sonda 69→41 ms, generació 57,6→97,2
t/s, passada 56→33 min) **sense cost de qualitat** dins el que tres passades permeten dir (code
−3,2 i agent +1,8 punts; tools igual; la dispersió del taulell és ±2-4). El global de l'OFF puja
+0,014 (0,819→0,833): el cap es paga per la via de la velocitat. La cama 1, a més, diu que els
sostres alts no mouen l'OFF (dims idèntiques als de la fila canònica amb 512), i la cama 3 que
comparar l'ON a 86016 amb el canònic a 233472 és just (0,798 vs 0,796; sonda 1075 vs 1060 ms).

**El preu del cap és context**: a 233472 no hi cap (KV de l'esborrany 456 MiB + graf 1220 MiB, i a
la targeta 0 n'hi havia ~1 GB); a 86016 hi cap de sobres. El sostre exacte amb cap no està
mesurat (entre 86k i 233k). Per això el perfil no el porta per defecte: el context és el que
aquest model ven al taulell, i la nota del perfil deixa la comanda preparada per a qui prefereixi
latència.

**No mesurat**: la cama 4 (ON amb cap), aturada a posta l'16-10 pel cost (~2-3 h) contra el que
aporta (mecanisme, no decisió). Nota per a qui ho repengui: en ON el coll és el pressupost de
32768 (6 topades a la cama 3, 0 a les dues OFF) i el cap no mou tokens, només rellotge — el que
s'hi guanyaria són hores de passada, no punts.

## 2026-10-16 (vespre) · Els pins de context màxim són de màquina tranquil·la

La suite ha caigut avui per una cosa que no era el codi: `test_smoke.py` aixeca un servidor de
debò amb el perfil de producció del model petit, i el d'UD-Q3 (`--spec-type draft-mtp --mmproj
-c 262144`) demana 1226 MiB per al graf de l'MTP i la targeta diu no. Amb el despatx actiu (~1,8
GB a la targeta 0), Heretic tampoc carrega a 233472: mor al mmproj (884 MiB); a 220k i a 212k
carrega, però amb 660 i 591 MiB lliures — per sota del marge de 1200 MiB que la sonda exigeix.

És a dir: les files ON de context màxim (Heretic, UD-Q3, qwen36, Ornith, qwen39, gemma) són
mesures de **màquina tranquil·la** — les vam fer de nit. Els rebuts són vàlids; el que no es
reprodueix és la condició. Si un run falla en arrencar amb `cudaMalloc ... out of memory`, és
això i no el codi: tancar el navegador, o baixar el pin. Verificat amb la sonda arreglada (que
ara, quan el sostre falla, comprova el terra abans de dir "none"): rebut complet a
`harness/logs/probe-context-smoke.log`.

Arreglat de passada, i és el que fa tornar la suite a verd:

- `ServerManager(extra_args=...)`: van al final, després del perfil — mateixa convenció que el
  propi perfil, o sigui que l'última paraula és del qui crida.
- El smoke carrega a `-c 8192`: la seva feina és la canonada (arrencar → xerrar → correctors),
  no validar el pin de producció; per a això ja hi ha el smoke de nivell 3 de
  `docs/verification.md`. 473 tests, verd, amb 1 salt (el del `--version`, que ja era).

**I el pin, baixat** (petició de l'usuari, 17:34): Heretic passa de `-c 233472` a **147456**.
Mesurat amb la sonda amb el despatx actiu i marge 2000 MiB: 196k→937 lliures, 170k→1509,
157k→1797, 150k→1961, i 144k→**2047**, l'únic que passa. Amb el marge estàndard de 1200 hi
cabria ~170k; s'ha triat 2000 perquè entre nit i dia el despatx bascula ~1 GB i encara hi ha
d'haver lloc per a un navegador. La fila ON (233472) queda com a rebut de màquina tranquil·la;
el proper run sortirà a 147456 i escriurà la seva pròpia condició (`ctx_resolved`), que és el
que el taulell llegeix. Si mai es vol més context, la variant d'~170k és a la nota del perfil.

## 2026-10-16 · Publicació del taulell v5 (README + gh-pages)

L'ordre era "publica el report actualitzat", i el report només era mitja veritat si la portada
del repo deia el contrari: el README encara anunciava *"One row so far"* per al conjunt v5 quan
al pool ja hi ha la re-mesura de l'estol sencer. Publicat, doncs, en dos passos:

- **README**: la secció del taulell porta ara la taula v5 completa (6 GGUF + Strata, OFF i ON =
  14 files, ordenades pel global com al CLI) amb el ★ del mode òptim. El text del voltant diu
  el que el report ja sap: 13 retirats (9+1+3, `harness/retired.json`), les files de context
  màxim són de màquina tranquil·la (el report imprimeix les banderes amb el `-c` de cada fila) i
  el pin diürn de l'Heretic (147456). **Dues files ON segueixen devent una passada justa** i ara
  ho diu la portada: gemma (sostres vells 256/2048) i Strata (512, 51 respostes buides).
- **`models/ASSIGNACIO.md`** (fora del repo, sense commit): la fila de l'Heretic deia que "el
  GGUF SÍ que declara MTP" — la nota falsa que em vaig empassar ahir — i portava el pin vell
  (262144). Ara diu 147456 (diürn), que **no té MTP**, i que el cap de la família existeix a
  part i dona 1,7× d'esborrany (A/B del 16-10). La capçalera recull l'excepció al criteri
  "pin = màxim mesurat en viu".

- **`harness/tools/publish-report.sh`** → gh-pages actualitzat (ref nou `7bf7c92`, el commit
  diu `main 937e862`). Verificat que no és un CDN enganyat: la pàgina servida és **byte a byte
  igual** al render local (`curl -o` + `diff`, 133262 bytes, IDENTICS). URL:
  <https://jordimarsal.github.io/ggufbench/>. `compare.html` s'ha enviat tal qual, que és el
  disseny del script (l'últim parell executat amb `--compare`).

## 2026-10-16 · Spec `report_polish` (polit del report) → Spec Gate

L'usuari demana tres canvis de polit al report publicat: (1) els models retirats, en una
pestanya HTML pròpia (avui s'intercalen en gris a *totes* les seccions: global, code,
agent, tools, speed, t/s, matriu, condicions), (2) les recomanacions just sota la franja
de KPIs, (3) tots els llistats d'stats, de millor a pitjor. Spec escrita en mode híbrid
(fem de spec-author): `harness/specs/report_polish/` — 12 R, 5 T en 3 tandes — i la
decisió de fons a **ADR-0010**: les pestanyes amb radios + CSS pur, sense cap script nou
(la pàgina manté el pressupost d'≤1 script i es llegeix sense JS). Decidit també a la
spec: la franja de KPIs passa a comptar *només* files vives (avui «Fastest 307 t/s» i
«Lowest latency 13 ms» els guanya el Nemotron, retirat) i la pestanya Retired és el
mirall del board, sense KPIs ni recomanacions (instruments d'elecció). Res de codi
tocat: **atura i espera el Spec Gate humà** (feature 8 = `spec_ready`).

## Next step

_If a new session opens: read AGENTS.md + current.md + feature_list.json. As of 2026-10-16 ~18:00
nothing is running, the GPUs are free and the report is published (section above); the A/B
receipts live in `results/runs/` (08:57, 16:41, 17:15) and `harness/logs/v5_ab_mtp/`. Pending on
the board: **gemma's ON row** still carries the old caps (256/2048, 22 empty) and **Strata's
ON** carries 512 (51 empty) — both deserve a pass with the fleet's raised caps (gemma is the
human's run; never llama-server and Strata together). Offered to the human, waiting on an
answer: refresh the three write-ups (`docs/writeups/*.md` are v4-era, title included) against
the v5 table. Optional: re-measure Heretic's ON row at its new 147456 pin (one night) so the
row matches the profile._ **Also pending: feature 8 `report_polish` (report tab polish) is
`spec_ready` — waiting on the human Spec Gate; see the section above and
`harness/specs/report_polish/`.**
