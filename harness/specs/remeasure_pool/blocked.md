# Blocked — remeasure_pool

**Data:** 2026-10-09 · **Estat:** in_progress → blocked (decisió del revisor)

**Motiu:** la re-mesura es va aturar al model 6/10 per decisió del revisor: amb el
conjunt de tasques actual (fins i tot amb el nivell hard), els models forts clusteritzen
dins ~8 punts (code 0.88-0.98, tools 0.75-1.00, agent 0.83-0.96 a les 5 entrades noves)
i el ranking bascula en 1-2 tasques. Re-mesurar ara obligaria a una TERCERA re-mesura
quan aterrin les tasques discriminants (feature 5 discriminative_tasks, pending).

**Evidència parcial conservada:** harness/logs/remeasure_pool/batch-llama.log
(5 models complets amb el protocol ADR-0001/0002: timeouts escalats, budget 16384,
0 exclusions de rellotge als densos 27B que abans en tenien 6-20).

**Estat del pool:** restaurat des de `results/models/pool.pre-remeasure.jsonl`
(condicions homogènies pre-re-mesura, marcador coherent si bé caducat).

**Desbloqueig:** quan discriminative_tasks passi el Completion Gate → tornar a
in_progress i executar T2-T5 (els logs de T1 serveixen de protocol de referència).
