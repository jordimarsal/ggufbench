# Quin model local hauria d'executar un agent de codi? Sis GGUFs i un motor Strata, un harness, rebuts

*També disponible en [anglès](which-local-model-for-coding-agents.md) i [castellà](which-local-model-for-coding-agents.es.md).*

Executo agents de codi al meu propi maquinari. llama.cpp en dues RTX 5080, models de la meva carpeta `models`, i una pregunta: quin GGUF, en quin quant, hauria de carregar abans de posar-me a treballar?

Els leaderboards públics mesuren una altra cosa. La majoria dels models hi estan entrenats, puntuen respostes d'un sol tret i no diuen res sobre si un model sap cridar una eina amb arguments ben formats, sobreviure a un bucle de diverses crides, llegir una carpeta, editar un fitxer i verificar el seu propi canvi. Aquesta és la feina que fa un agent tot el dia, així que vaig deixar de llegir aquestes taules per a aquesta decisió i vaig construir [ggufbench](https://github.com/jordimp/ggufbench).

Un harness, les mateixes condicions, quatre dimensions i els rebuts en brut de cada crida — aquesta ronda, sis GGUFs sota llama.cpp i un model sota el motor [Strata](https://github.com/Niko1221/Strata), cadascun en els dos modes de thinking.

## Les regles que fan que els números signifiquin alguna cosa

Cada model s'executa amb el mateix mostreig: temperatura 0.2, top-p 0.95, top-k 40, min-p 0.05, llavor 42, KV cache q8_0, `--jinja`, un sol slot. Cada valor del mostreig està fixat explícitament, perquè un GGUF porta la seva pròpia metadata de mostreig — aquesta flota sola embarca tres valors diferents de `top_k` (20, 64 i cap) — i un valor no fixat no és una condició compartida sinó una de per model. Els ajustos estan fixats en dos llocs, els flags del servidor i el cos de la petició, perquè una deriva de configuració al servidor no es coli en una comparació.

Cada model conserva el seu fitxer de perfil. Aquest perfil s'aplica al final i pot sobreescriure la línia base, així que els models competeixen en la seva millor configuració real i no en un muntatge de laboratori que hagi inventat jo. El harness fixa els flags d'infraestructura, i allò amb què va acabar corrent cada model queda registrat a la seva fila de resultat.

Les exclusions s'anoten amb un motiu. Un model que esgota el temps o respon amb prosa on s'esperava un bloc de codi no desapareix en silenci de la mitjana; surt a l'informe, comptat.

El harness només fa servir la biblioteca estàndard de Python. Cap arbre de dependències que es podreixi mentre el benchmark espera.

Cada tasca guarda tres execucions, llavors 42, 43 i 44, i el marcador informa de mitjana ± desviació estàndard. Quan una fila diu `0.85 ±1`, aquesta dispersió forma part de la resposta.

## Què va dir el marcador

El pool actual executa el conjunt v5: 18 tasques d'eines, 72 de codi en quatre llenguatges (32 fàcils, 20 difícils, 20 expertes), 72 tasques d'agent multipas (13 de les quals projectes de diversos fitxers) i 32K de pressupost de sortida per al codi. Les files de sota es van mesurar la nit del 2026-10-14/15. La part alta de la taula:

| model | think | eines | codi | agent | velocitat | global |
| --- | --- | --- | --- | --- | --- | --- |
| minicpm-v-4.7-35b-a3b q4_k_m | on | 100% ±0 | 82% ±4 *(8 excl.)* | 89% ±0 | 23ms | **0.85 ±1** |
| minicpm-v-4.7-35b-a3b q4_k_m | off ★ | 100% ±0 | 83% ±1 *(2 excl.)* | 90% ±2 | 26ms | **0.85 ±0** |
| qwen36-35b-distill-mxfp4_moe | off ★ | 94% ±0 | 74% ±3 | 92% ±2 | 19ms | 0.84 ±1 |
| qwen3.8-27b-ud-q3_k_xl | off | 100% ±0 | 79% ±4 | 90% ±1 | 36ms | 0.82 ±1 |
| ornith-1.5-35b-a3b-apex-mtp-quality | off ★ | 100% ±0 | 75% ±2 | 92% ±1 | 32ms | 0.82 ±1 |
| qwen3.8-27b-heretic-q4_k_m | off ★ | 100% ±0 | 86% ±2 | 92% ±2 | 85ms | 0.81 ±1 |
| qwen3.8-27b-ud-q3_k_xl | on | 94% ±0 | 93% ±1 *(1 excl.)* | 96% ±1 | 629ms | 0.80 ±0 |
| gemma-4-26b-a4b-it-ud-q5_k_xl | off ★ | 89% ±0 | 86% ±1 | 87% ±2 | 33ms | 0.80 ±0 |
| strata-iq3_xxs *(strata engine)* | off ★ | 91% ±6 | 85% ±1 | 92% ±1 | 45ms | 0.80 ±1 |
| qwen3.8-27b-heretic-q4_k_m | on | 94% ±0 | 90% ±2 | 97% ±1 | 1060ms | 0.80 ±0 |

*★ = el mode thinking òptim de cada model segons les dades: qualitat dins de ±0.02 de l'altre mode i sense més temps de rellotge; els empats exactes van a off.*

Tres coses van destacar.

### Les primeres files són empats

Les deu primeres files abasten cinc centèsimes — de 0.85 a 0.80 — i les files veïnes queden com a màxim a una o dues centèsimes, de la mateixa mida que la dispersió entre tirades que acompanya cada puntuació. La puntuació global ordena una flota; no certifica que la fila 1 superi la 7. Qui ordeni dues files properes pel segon decimal està citant soroll.

### El mode thinking és un impost que només paga al codi difícil

Ho vaig mesurar com a files separades en lloc de fondre-ho en un sol número. Thinking on multiplica la latència per torn — cada fila on excepte la del MiniCPM corre entre 280 i 1060 ms contra els 19–85 ms de off (la on del MiniCPM aterra als 23 ms) — i també costa qualitat a tots els models, amb el MiniCPM com a únic empat. A més, concentra les exclusions: de les 1.512 execucions de codi de la flota per mode, off n'exclou 6 i on n'exclou 101, la majoria respostes sense bloc de codi on se n'esperava un (tasques completament excloses: 2 contra 14).

On sí que compra alguna cosa és al nivell difícil de codi: l'UD-Q3 puja del 79% al 93% en el codi global (92% difícil, 91% expert), l'Ornith +10 punts sobre el seu propi off, l'Strata +6, l'Heretic +4 — i el bucle d'agent de l'Heretic arriba al 97%, el millor de la flota. A les tasques que ho necessiten, el thinking val deu vegades l'espera; a la resta, és un impost sense retorn visible.

### Les tasques fàcils de codi no discriminen

Amb thinking off, tota la flota aterra entre el 91% i el 100% al nivell fàcil, mentre que difícil i expert viuen entre el 47% i el 87%. La separació és en aquests dos nivells — sobretot a les expertes, construïdes amb depuració de diversos errors i contractes de sortida estrictes (tornar el fitxer complet corregit, arrodoniment exacte, còpies defensives). El marcador fon els tres nivells en una columna de codi; el desglossament per nivell que registra (`by_level`) és on viu la discussió.

## Què et recomanaria fer

Tria per dimensió. En aquesta taula, les eines són del MiniCPM (100%), el codi difícil de l'UD-Q3 amb thinking (92% difícil, 91% expert), el bucle d'agent de l'Heretic amb thinking (97%) i la velocitat per torn del qwen36 off (19 ms). Cap fila ho guanya tot.

Mesura al teu maquinari amb els teus propis perfils. Un quant que va còmode en dues 5080 és una presentació de diapositives en una, i el resultat canvia amb la configuració del KV cache.

Llegeix les exclusions. Un model que falla a l'hora de formatar una crida d'eina de tant en tant no és una mica pitjor que un que sempre l'encerta. En un bucle d'agent, l'atura.

Tracta les files properes com a empats. Deu files dins de cinc centèsimes no són una classificació, són un grup. Trio dins seu per latència i per com es comporta un model quan falla una crida, no pel tercer decimal d'una puntuació.

## La lletra petita

Les tasques estan escrites per a aquest harness, les solucions de referència no surten mai de la màquina i els models sota prova són els quants de GPU de consum que la gent executa. Les puntuacions responen a "quin GGUF hauria d'executar per a treball agentic", no a "com n'és de llest aquest model". Dues files thinking-on (gemma, strata) es van mesurar amb límits de cridades més estrets que la resta i l'informe les marca com a pendents d'una passada justa; els tretze models retirats pel camí viuen a la seva pestanya Retired, només registre. Mètode complet a `docs/SPEC.md` del repositori.

Marcador i informe en directe: [jordimp.github.io/ggufbench](https://jordimp.github.io/ggufbench/).
Codi, tasques i rebuts: [github.com/jordimp/ggufbench](https://github.com/jordimp/ggufbench).
