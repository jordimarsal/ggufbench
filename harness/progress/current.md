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


- **Ad-hoc (11-oct, cont.): ngram (lookup) drafting a UD-Q3** — copy-heavy probe
  propi (mòdul de 65 línies + rename): ngram-map-k4v 352,3 t/s vs MTP n4 139,5 (2,5×);
  text nou 51,2 vs 113-127 (sense guany). Exclusius per servidor. Perfil es queda
  MTP n4 (trànsit mixt); ngram documentat a la skill per a sessions d'edició.
  Nota tècnica: els intents aïllats en zsh fallien per word-splitting (zsh no
  splitteja $BASE) — els sweeps han de córrer amb bash.


- **Ad-hoc (11-oct, cont.): sweep MTP/split a la flota** (eines a bin/mtp-sweep.py +
  bin/mtp-probe.py, del repo qwen38-mtp): tensor-split +25-45% als 4 splitters
  (udq5/heretic/turbofcf/coder390), n4 guanyador (+3-6% vs n3), n6 mata la prosa.
  Flags aplicats als .txt: --spec-draft-n-max 4 + --split-mode tensor (UD-Q3 només n4,
  13 GB gairebé single-GPU; tensor sense provar). ATENCIÓ: files del pool d'aquests 4
  models queden STALE (condicions de serving canviades) — re-mesura pendent quan es
  vulgui (no ara, ordre humana).


- **Ad-hoc (11-oct, cont.): tuning reserve Strata 0.1.42** — res 1400 perdia decode
  OFF (89,3 t/s); res 1000 passa la verificació i guanya a tot: OFF 116,1 t/s gen
  (+8%), prefill 169,4 (+17%), 43 ms; ON 125,4 t/s (+14%), 465 ms, 0 excloses, code
  0.93. Config final fixada: reserve 1000. Skill llama-slots §6f documentada.

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
