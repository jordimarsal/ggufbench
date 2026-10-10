# Completion Gate — discriminative_tasks

**Data:** 2026-10-10 · **Decisió:** APPROVED amb canvis (in_progress → done)

Checklist del gate (docs/verification.md):

- [x] Totes les tasques `[x]` a `tasks.md` (10/10), amb logs de batch a
  `harness/logs/discriminative_tasks/batch-{1..7}.log` + `author-validation.log` +
  `smoke-r5.log` / `smoke-r5-attempt1.log`.
- [x] Traçabilitat objectiva: `check-traceability.py --feature discriminative_tasks`
  → 7/7 PASS (`traceability-check.txt`); `--all` → PASS.
- [x] Gates executats en primera persona: suite unittest (165 tests OK, 1 skip
  preexistent) + `harness/init.sh` verd (`batch-7.log`).
- [x] Validació d'autor de les 12 tasques expert: ref OK, partial FALLA al tercer
  comportament (`author-validation.log`; solucions a /tmp, no commitades).
- [x] Fum R5 amb 2 models reals: 2 tasques expert separen ✓/✗ amb gap 100
  (`harness/specs/discriminative_tasks/smoke-r5.md`, test mecànic
  `tests/test_smoke_evidence.py`).
- [x] Review propi (`review.md`): veredicte APPROVED + checklist de seguretat basic
  confirmat + 4 observacions (D6, sostre de tokens/think, remaps d'IDs, pool restaurat).
- [x] Commits: `aabff88` (tier expert) + `19305d9` (docs) + `4dc88ec` (harness).
- [x] Aprovació humana registrada a `APPROVAL` (amb el canvi Q1: pressupost code
  inicia a 32768, a implementar a la feature següent).

Tancament per flow: resum mogut a `harness/progress/history.md`; següent feature:
**thinking_batches** (nova: doble batch think/no-think + pressupost 32768 + exclosos
senyalitzats + clau de pool per `(slug, thinking)`) — la re-mesura no comença fins al
seu Completion Gate (`remeasure_pool` continua `blocked`).
