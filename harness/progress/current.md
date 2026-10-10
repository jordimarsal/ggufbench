# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** remeasure_pool (id 2, in_progress — desbloquejat 2026-10-10)
- **Started:** 2026-10-10
- **Agent:** hybrid (un agent, rols sequencials)

## Plan

- T1 pre-flight (servidors morts, ports lliures, suite verda, pool homogeni v1,
  perfils `-c`, config Strata, sonda del kwarg contra llama-server) → preflight.log.
- T2 batch llama OFF (10 models, dims completes, tots els nivells) → batch-llama-off.log.
- T3 batch Strata OFF (`iq3_xxs`, només quan cap llama-server quedi viu) → batch-strata-off.log.
- T2b/T3b ídem amb `--thinking on` → batch-llama-on.log / batch-strata-on.log.
- T4 verificació (pool amb les dues claus, by_level, tasks_version, report sense
  banner espuri) + T5 summary.log + traçabilitat + Completion Gate.

## Log

- `thinking_batches` tancada (done, gate sense canvis, `4c3d010`).
- `remeasure_pool` → in_progress; `blocked.md` amb l'historial de blocatge+desbloqueig.
- **T1 pre-flight (verificat):** cap servidor viu, ports lliures, `init.sh` verd
  (187 passed → `preflight.log`), pool homogeni v1 (`diff` buit vs pre-remeasure),
  `strata-iq3_xxs.json` present, `-c 65536` als 3 perfils. **Sonda:** llama-server
  retorna HTTP 200 amb i sense `chat_template_kwargs.enable_thinking=false` (8B) —
  el batch OFF mesura amb thinking desactivat de debò. T1 tickat.
- **T2 batch llama OFF llançat** (10 models, dims/levels complets, `--thinking off`,
  32768 tok, cap 1000s) → `batch-llama-off.log` (background). Ordre després: Strata
  OFF → llama ON → Strata ON (mai dos motors alhora).
- **T2 complet (exit 0, ~31 min):** 10/10 ✓, 0 `serve_failed`, 0 `server error`.
  Pool: 10× `(off, v3)` + 11 legacy `(None, v1)` coexistint (clau nova OK).
  Netejats 24 `*-m/other-off.json` (brossa dels tests al dir real — deute pre-existent:
  els tests canvien POOL_FILE però no RESULTS_RUNS). T2 tickat.
- **T3 Strata OFF llançat** (`--engine strata --models iq3_xxs --thinking off`) →
  `batch-strata-off.log` (verificat: cap llama-server viu, port lliure).
- **T3 complet (exit 0):** strata-iq3_xxs off/v3 amb code=0.95 (resol bé les expert);
  pool amb les dues files strata (legacy v1 + off v3). Cap Strata viu després. T3 tickat.
- **Batch llama ON llançat** (mateixos 10 models, `--thinking on`, pensament lliure) →
  `batch-llama-on.log` (background). Després: Strata ON i T4 (verificació).
- **Batch llama ON complet (10/10):** 3 primers + restart de 7 per mort prematura del
  procés (12:26, causa indeterminada; `setsid+faulthandler` estable ~5 h). Pool: 32
  files (11 legacy v1 + 11 off v3 + 10 on v3). ON vs OFF en code: UD-Q5 0.96 vs 0.82,
  UD-Q3 0.95 vs 0.87 (pensar ajuda els forts); MoE 0.78 amb 5 excloses (el think crema
  pressupost als petits). T2 anotat on.
- **Strata ON llançat** (`--engine strata --models iq3_xxs --thinking on`, sense
  EXTRA_BODY → HIGH lliure) → `batch-strata-on.log` (verificat: cap llama viu).
- **Incident 12:26: el batch ON va morir en silenci a 3/10** (model 4, Heretic, a mitges
  de java; servidor orfe a GPU, pool intacte amb 3 ON desades, sense OOM visible).
  Causa indeterminable sense root. Resposta: orfe matat per PID, rellançament dels 7
  restants amb `setsid nohup` + `python3 -X faulthandler` (separador RESTART al mateix
  log; si torna a caure, hi haurà traça). Dada lateral: MoE-ON porta 5 excloses en code
  (el think crema pressupost — hipòtesi confirmada en directe).

## Next step

Esperar el batch llama OFF (notificació automàtica). Verificar: 10 models ✓ al log,
fitxers `results/runs/*-off.json`, `thinking: "off"` a cada fila, 0 `serve_failed`.
Després Strata OFF (`--engine strata --models iq3_xxs --thinking off`).
