# Requirements: discriminative_tasks

La re-mesura de 2026-10-09 ho confirma amb dades: ni les fàcils ni les hard separen els
models forts. Amb el nivell hard aterra, el top-5 clusteritza dins ~8 punts (code
0.88-0.98, tools 0.75-1.00, agent 0.83-0.96) i el ranking bascula en 1-2 tasques.
Aquesta feature afegeix el nivell **expert**: tasques més difícils i més llargues
(multi-fitxer, context proveït, sortides de mòdul sencer) que exigeixin consolidar
múltiples comportaments — el tipus de feina que distingeix models forts.

## R1
The system shall assign code tasks an `level` of `"expert"` when their `ID` ends with
`_expert`, and `run.py --level` shall accept `easy|hard|expert` (default: all levels
folded, same policy as the hard tier).

## R2
Tasks shall be able to declare `EXTRA_FILES` (a dict of support files), and the system
shall write those files into the sandbox alongside the solution and the test before
running it.

## R3
The system shall ship at least 3 expert tasks per language (python, bash, java,
typescript), each of them multi-part (at least 3 related behaviours to satisfy
simultaneously) and/or with at least 80 lines of provided context (embedded in `PROMPT`
or via `EXTRA_FILES`), whose `TEST_CODE` fails on partial or naive solutions.

## R4
The code result shall include the expert level in its `by_level` breakdown, the HTML
report shall display it, and `tasks_version` shall bump to `"v3"` (the pool must tell
this task set apart).

## R5
The feature shall demonstrate discrimination: in a smoke with at least 2 models, at
least one expert task shall separate the models by 20 points or more.

## R6
The system shall not modify the global weights, the other dimensions, or the folding
policy of the existing levels.

## R7 (retired 2026-10-09)
L'antic requisit de puntuar l'eficiència (tokens per tasca) es jubila: ja existeix com
a mètrica registrada (`out_tokens`, feature timeout_scaling/ADR-0002) i puntuar-la seria
una dimensió nova — fora d'abast aquí. Els IDs no es reutilitzen.
