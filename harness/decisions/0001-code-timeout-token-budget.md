# ADR-0001: El pressupost d'una tasca de codi és en tokens; el rellotge només és guarda anti-penjam

- **Date:** 2026-10-09
- **Status:** accepted
- **Feature:** timeout_scaling

## Context

Amb el timeout fix de 60 s per petició, els models que generen a 38-44 t/s i **pensen**
(Qwen3.8 amb `--jinja`: pensament activat de fàbrica) es queden sense cobertura a les
tasques de codi llargues — sobretot les hard: el timeout expira mentre el model encara
està produint tokens legalment. A la re-mesura de 2026-10-09, un model va acumular 20
exclusions d'aquest tipus a mig run. L'exclusió no abaixa el score, però elimina
cobertura: la mostra publicable queda sesgada cap als models ràpids, i la pèrdua
correlaciona amb la velocitat — exactament el biaix silenciós que un benchmark no es
pot permetre.

## Decision

El pressupost real d'una tasca de codi és el de **tokens** (`CODE_LADDER`, igual per a
tot el món). El timeout de cada intent es deriva de la velocitat **mesurada** del model
propia: `code_timeout(budget, gen_tps) = clamp(90, 60 + (budget/gen_tps)*1.25, 600)`
segons, i 90 s fixes si no hi ha velocitat mesurada. Un timeout (ara com abans) és una
**exclusió**, mai una falla.

## Alternatives considered

- **Timeout pla generós (300 s)** — simple, però un model a 130 t/s rep 12 vegades més
  pressupost de tokens real que un a 38 t/s: mateixa injustícia, més amagada.
- **Desactivar el pensament a tots els models** (`enable_thinking=false`) — canviaria
  QUÈ es mesura (el model tal com ve de fàbrica) i treuria informació; queda com a
  possible decisió de política futura, no com a pegat de timeouts.
- **No fer res** — el marcador publicable queda amb cobertura correlacionada amb
  velocitat: descartat explícitament.

## Consequences

- Els models lents ara triguen més a mesurar-se (així és com es venen ells mateixos):
  la re-mesura completa pot allargar-se. La dimensió **speed** (0.15) continua sent
  l'única que puntuarà la velocitat.
- La fórmula viu a `graders.code_timeout` i es testeja (pis 90 s, sostre 600 s,
  fallback sense `gen_tps`): barata de revertir si apareix un criteri millor.
- Qualsevol canvi futur de pressupostos (`CODE_LADDER`) arrossega automàticament el
  timeout — una cosa menys que recordar.
- Reversibilitat: barata (una funció pura + un paràmetre).
