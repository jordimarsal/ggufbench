# Requirements: remeasure_pool

El pool actual barreja condicions: els 10 models llama van córrer amb dues tasques
impossibles (get_env/get_time) i l'agent java trencat (0.00 per a tots); Strata hi és
mesurat post-fix però sense nivell hard. Amb el harness arreglat i el nivell hard a
l'abast (tasks_version v2), tot el pool ha de tornar a mesurar-se per tenir un marcador
homogeni i publicable.

## R1
The system shall re-measure every model present in the pool at the start of the
re-measure (10 llama-server models + `strata-iq3_xxs`) with the current harness
(`tasks_version` v2, nivell hard inclòs, sense `--level`: fàcils + hard plegades).

## R2
The system shall not run llama-server and Strata at the same time: the llama batch
(`--models all`) shall complete and stop its server before the Strata invocation starts.

## R3
When the re-measure finishes, the pool shall contain exactly the re-measured entries
(one per model, upsert per slug, cap entrada d'una condició anterior).

## R4
When the pool is regenerated, the system shall rebuild `results/report.html` from it, and
the mixed-conditions banner shall not appear (totes les entrades d'una mateixa sessió).

## R5
The re-measure evidence (ordres, inici/fi de cada model, sortida del scoreboard final)
shall be recorded under `harness/logs/remeasure_pool/` abans de demanar el Completion
Gate.
