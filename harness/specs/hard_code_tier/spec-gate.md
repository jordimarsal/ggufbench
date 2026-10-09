# Spec Gate — hard_code_tier

**Data:** 2026-10-09
**Decisió:** APPROVED (pending → spec_ready → in_progress)

- Revisor: Jordi (human gate, via assistent de sessió).
- Entrada revisada: `requirements.md` (R1-R8) + `design.md` (fitxers, signatures,
  casos d'error, 5 alternatives descartades) + `tasks.md` (12 tasques, 6 batches).
- Decisions preses pel revisor abans de l'spec:
  - 4 tasques hard per llengua (16 en total) a la primera iteració.
  - Score plegat dins de code (mateixa dimensió i pesos), desglossament by_level al
    report.
- Sortida: implementació per batches amb evidències a `harness/logs/hard_code_tier/`.
  Completion Gate requerirà traçabilitat R1-R8 completa + `harness/init.sh` verd.
