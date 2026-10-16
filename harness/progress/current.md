# Current session

> This file is cleared on session close and moved to `history.md`.
> Keep it updated in real time while you work — not at the end.

- **Feature in progress:** _none_ (all 8 `done`; `lora_eval` = feature 7 `spec_ready`,
  waiting on the human Spec Gate)
- **Started:** _—_ (ad-hoc docs work, 2026-10-16 nit: write-ups refresh)
- **Agent:** in-session

## Plan

_Describe in 3-5 bullets what you will do before touching code._

## Log

_Note each significant step: files created, decisions, blockers._

- **Ad-hoc (humà: «actualitza els write-ups»)** — refresc dels tres
  `docs/writeups/which-local-model-for-coding-agents.{md,ca,es.md}` contra el taulell v5,
  sense canvis de codi:
  - títol: «Nine GGUFs» → «Six GGUFs and a Strata engine» (flota viva = 6 GGUF + Strata);
  - conjunt: v3 16/60(32/16/12)/42 → **v5 18/72(32/20/20)/72** (13 projectes multi-fitxer,
    32K de pressupost de codi), files mesurades la nit del 10-14/15;
  - taula amb columna `think` (top 10, igual que el README) + nota del ★ (C8);
  - secció thinking reescrita amb dades v5: latència 280–1060 ms vs 19–85 ms, **101 vs 6
    tirades excloses** de 1.512 per mode (2 vs 14 tasques excloses del tot), i el guany real
    al codi difícil (UD-Q3 79→93 global, 92 difícil/91 expert; Ornith +10, strata +6,
    Heretic +4; agent d'Heretic 97%);
  - empats: deu files dins de 5 centèsimes, veïns a 1–2 centèsimes, mida comparable a la
    dispersió per tirada (stdevs calculats del pool: ±0.2–1.4);
  - fàcils 91–100% off vs difícil/expert 47–87%; recomanacions concretes per dimensió;
  - lletra petita: files ON de gemma/strata pendents de passada justa + pestanya Retired.
- Verificat: 3 fitxers de 73 línies, 8 encapçalaments i les mateixes 10 files a les tres
  llengües (conjunts numèrics iguals; `1.512`/`1,512` és el separador de milers).

## Next step

_If the session is interrupted, this is what the next session should do first._

_Pending from the 2026-10-16 close (details in `history.md`, tail): gemma ON + Strata ON
deserve a pass at the fleet's caps; Heretic ON re-measure at 147456 (one night); the
write-ups refresh offer awaits the human; `lora_eval` waits on its Spec Gate._
