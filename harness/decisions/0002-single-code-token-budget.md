# ADR-0002: Un únic pressupost generós de tokens per a les tasques de codi (fi de l'escala)

- **Date:** 2026-10-09
- **Status:** accepted
- **Feature:** single_token_budget (proposta del revisor en plena re-mesura)

## Context

L'escala `CODE_LADDER = [2048, 4096, 8192]` va néixer per mesurar models sense cadena
de pensament: si el bloc no cabia en 2048 tokens, s'escalava. Amb models que **pensen**
(Qwen3.8, pensament de fàbrica amb `--jinja`), el primer intent gasta sovint 1000-2000
tokens només en raonament: l'escala es converteix en 1-2 peticions malgastades per
tasca (el resultat final és idèntic, però pagat tres vegades en wall-clock).

## Decision

Un únic pressupost per a totes les tasques de codi: `CODE_MAX_TOKENS = 16384`,
`CODE_LADDER = [16384]` — el sostre del context del harness (`CONTEXT_FIXED` menys
prompt), que és el `2×8192` proposat pel revisor absorbit com a pressupost únic. Clau
tècnica: amb seed/temp fixos, `max_tokens` és un **sostre, no un objectiu** — un intent
a 16384 reprodueix la mateixa generació que qualsevol escala inferior (prefix
determinista), així que el score és demostrablement idèntic i només s'elimina el temps
mort. L'eficiència (tokens de sortida per tasca) queda registrada a la traça
(`out_tokens`) com a mètrica informativa, mai com a càstig.

## Alternatives considered

- **Mantenir l'escala original [2048, 4096, 8192]** — 1-2 peticions mortes per tasca
  en models que pensen: descartat per pur overhead.
- **Escala [8192, 16384]** — mateix resultat que l'únic 16384 (prefix determinista) però
  reintrodueix l'escala i els bucles degenerats costen 2 intents (329+598 s) en lloc
  d'un (598 s, dins el guarda d'ADR-0001): descartat.
- **8192 únic (primera versió d'aquest ADR)** — deixava sense mesurar la cua de
  pensament llarg (8-16k tokens) dels models que pensen: descartat pel revisor.

## Consequences

- Menys peticions i menys temps per run amb models que pensen; models concisos no
  canvien (para a l'EOS igualment).
- `token_budgets.json` perd la meitat del sentit (el "pressupost calibrat" sempre serà
  8192 o no hi arribarà): es manté el mecanisme per compatibilitat i per si torna un
  pressupost escalonat.
- La verbositat deixa de ser un sostre dur i passa a ser mètrica: si demanés puntuar-la,
  seria una dimensió nova explicita, no un efecte colateral del timeout.
- Reversibilitat: barata (una constant + un test).
