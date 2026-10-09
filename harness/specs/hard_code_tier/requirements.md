# Requirements: hard_code_tier

Avui les 32 tasques de code són trivials: tots els models seriosos fan 84-100% i la
dimensió amb més pes (0.30) no discrimina. Aquesta feature afegeix un nivell **hard**
(4 tasques per llengua, 16 en total) plegat dins la dimensió code, sense canviar pesos
ni la resta de dimensions.

## R1
The system shall assign each code task a `level` of `"hard"` when its `ID` ends with
`_hard`, and `"easy"` otherwise.

## R2
When `--level {easy,hard}` is given, the system shall run only the code tasks whose
`level` matches, leaving speed, tools and agent dimensions unchanged.

## R3
When no `--level` is given, the system shall run easy and hard code tasks together and
compute the code score over all of them (folded: same weight per task, dimension weight
unchanged).

## R4
The code result shall include a `by_level` breakdown (`{"easy": score, "hard": score}`)
computed only over the tasks of each level that were actually run.

## R5
The HTML report shall display the code `by_level` split for every model that has one.

## R6
The system shall ship 4 hard code tasks per language (python, bash, java, typescript),
each with an `ID` ending in `_hard`, a `PROMPT` that requires fixing/optimizing/implementing
non-trivial logic, and a `TEST_CODE` that runs in the sandbox and fails on the naive
solution.

## R7
When the code task set changes with this feature, the system shall record
`tasks_version` `"v2"` in every new result (the pool must be able to tell pre/post
conditions apart).

## R8
The system shall not modify the score semantics of existing easy tasks, the global
weights (`tools 0.30, code 0.30, agent 0.25, speed 0.15`) or any other dimension.
