# Spec Gate — timeout_scaling

**Data:** 2026-10-09 · **Decisió:** APPROVED (pending → spec_ready)

Revisor: Jordi (human gate). L'aprovació inclou la fórmula exacta escollida
explicitament pel revisor en plena execució de remeasure_pool:
`clamp(90, 60 + (budget/gen_tps)*1.25, 600)`, mantenint les exclusions com a
semàntica, més ADR-0001. Operativa aprovada: aturar la re-mesura en curs,
implementar, i repetir la re-mesura sencera amb el protocol nou.
