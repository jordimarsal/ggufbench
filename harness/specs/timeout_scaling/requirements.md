# Requirements: timeout_scaling

Amb el timeout fix de 60 s, els models lents que pensen (38-44 t/s) es queden sense
cobertura a les tasques hard: el timeout expira mentre encara generen tokens legalment.
El pressupost real d'una tasca de codi ha de ser en tokens (mateix per a tots els models)
i el rellotge només una guarda anti-penjam derivada de la velocitat mesurada.

## R1
The system shall compute the per-attempt code chat timeout as
`code_timeout(budget, gen_tps) = clamp(90, 60 + (budget / gen_tps) * 1.25, 600)` seconds,
and shall use 90 seconds when no `gen_tps` is available.

## R2
The system shall pass that timeout to every chat attempt of the code escalation ladder
(2048, 4096, 8192 tokens), while speed, tools and agent dimensions keep their existing
timeouts.

## R3
The system shall keep recording timeouts as exclusions (never as fails): only the wait
changes, not the score semantics.

## Requisit jubilat (2026-10-09)

L'antic quart requisit (registrar la decisió com a ADR-0001) es jubila: un ADR no és
verificable per test (regla EARS 2) i per tant no és un requisit vàlid. L'ADR-0001
existeix com a artefacte de `design.md`/T3 a `harness/decisions/` i es revisa a la
review. Els IDs no es reutilitzen.

## R5
The unit suite shall cover the timeout formula (floor, ceiling, no-tps fallback) and
that `grade_code` hands the scaled timeout to the client.
