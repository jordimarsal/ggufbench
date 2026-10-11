# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (totes 6 `done`; 2026-10-10 + ad-hoc post-sessió)
- **Started:** _—_
- **Agent:** _—_

## Plan

_Tria la pròxima feina (candidats: anàlisi out_tokens ON vs OFF promesa al checkpoint;
agent multi-fitxer C4; P0 README/CI de MILLORA)._

## Log

- **Ad-hoc (11-oct): Strata 0.1.41 → 0.1.42** (`./update.sh`, engine recompilat, configs
  intactes amb el budget de la §6g). Primera arrencada fallava: la nova verificació
  (arena 70 MiB) no capia a CUDA0 (cache PROFILE 5232 slots sobre-commitava; auto hauria
  posat 3745). Fix: `--vram-reserve-mib 1400` a strata-iq3_xxs.json (DETAILS §cache).
  Smoke verd: health, models, chat amb chat_template_kwargs, tancat net.
- **Ad-hoc (10-oct): Coder390 al pool** (OFF+ON): claim "-53% tokens" CONFIRMAT vs
  germans 27B (2.084 vs 4.2-4.4K tok), 0 excloses en ON, code ON 0.95. Skill
  llama-slots: reserva ON preferida. Files 0.1.41 de strata respades a
  harness/logs/remeasure_pool/strata-0.1.41-rows.json abans de mesurar 0.1.42.

- **Ad-hoc (ordre humana directa, fora de gates):** anàlisi out_tokens ON vs OFF
  (659 instàncies aparellades) + `fix(html_report)`: text llegible a la matriu
  (fons sòlid per lluminància, fora alfa) + badge think a les 8 seccions per model.
  Suite 189 passed. Commit `089eeb5`. report.html regenerat (22 badges/mode).

## Next step

_Si s'obre sessió nova: llegir AGENTS.md + current.md + feature_list.json._
