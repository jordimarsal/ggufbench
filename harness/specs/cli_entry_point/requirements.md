# cli_entry_point — Requirements

## Context

Fase 4b d'`estol` (drafts/10-estol-malla-equips.md §15, pas 0): el nodelet necessita
executar benchmarks com a job tancat. La CLI ja existeix (`run.py` amb `main(argv)`,
coberta per `tests/test_run_cli.py`) però només és invocable com
`python3 -m ggufbench.run` des de l'arrel del workspace. Falta l'entry point de paquet.

## Requisits (EARS)

- **R1:** QUAN el paquet s'instal·la (pip/uv), EL SISTEMA exposarà el script de consola
  `ggufbench` equivalent a `python3 -m ggufbench.run`.
- **R2:** QUAN s'executa `python3 -m ggufbench.run` des de l'arrel del workspace, EL
  SISTEMA es comportarà exactament igual que abans (cap canvi de comportament).
- **R3:** QUAN s'instal·la editable des del checkout de bench (`~/ia/llama/ggufbench`),
  EL SISTEMA resoldrà `MODELS_DIR`/`RESULTS_DIR`/`SERVER_BIN` al mateix lloc que avui
  (via `__file__`, mai site-packages).
- **R4:** EL SISTEMA s'instal·larà sense dependències de tercers (stdlib pur: el venv de
  l'eina queda hermètic) i la suite unittest completa passarà verda, sense GPU
  (gate `harness/init.sh`; evidència al log del batch).

## Fora d'abast

- Noves flags ni subcomandes (`run`/`report` com a subcomanda NO existeixen i no es
  creen: el contracte real és `ggufbench --models <nom>` — ho consumeix el lane d'estol).
- Empaquetatge de dades (tasks/, models/, harness/) dins la distribució: la instal·lació
  és editable des del checkout, que ja les té.
