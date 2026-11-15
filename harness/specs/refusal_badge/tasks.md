# Tasks: refusal_badge

- [ ] T1: `probe-refusal.py --save` → `results/refusal/<slug>.json` amb `slug` +
      `generated_at`; `--json` intacte. Tests: slug per label extern (strata), creació
      de directori, sobreescriptura d'un resultat previ, `--save` sense `--models` →
      error d'ús.
      depends_on: (none)
      refs: R7
- [ ] T2: cel·la del marcador CLI — `report.refusal_cell(r)` amb cache per render,
      `—` si no hi ha dades (R2), `~` si antic (R3), PIN R4 (globals idèntics amb i
      sense dades, test de byte-comparació), degradació sense directori (R6).
      Tests: present, absent, stale, missing-dir, r4-pin.
      depends_on: T1
      refs: R1, R2, R3, R4, R6
- [ ] T3: badge HTML + title per categoria + amplada de cel·la del CLI + README
      (screening, mai pes) + entrada a docs/specs.md. Tests: badge present/absent,
      title amb resum per categoria, degradació.
      depends_on: T2
      refs: R1, R2, R5, R6
