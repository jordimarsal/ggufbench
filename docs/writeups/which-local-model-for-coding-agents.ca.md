# Quin model local hauria d'executar un agent de codi? Nou GGUFs, un harness, rebuts

*També disponible en [anglès](which-local-model-for-coding-agents.md) i [castellà](which-local-model-for-coding-agents.es.md).*

Executo agents de codi al meu propi maquinari. llama.cpp en dues RTX 5080, models de la meva carpeta `models`, i una pregunta: quin GGUF, en quin quant, hauria de carregar abans de posar-me a treballar?

Els leaderboards públics mesuren una altra cosa. La majoria dels models hi estan entrenats, puntuen respostes d'un sol tret i no diuen res sobre si un model sap cridar una eina amb arguments ben formats, sobreviure a un bucle de diverses crides, llegir una carpeta, editar un fitxer i verificar el seu propi canvi. Aquesta és la feina que fa un agent tot el dia, així que vaig deixar de llegir aquestes taules per a aquesta decisió i vaig construir [ggufbench](https://github.com/jordimarsal/ggufbench).

Un harness, les mateixes condicions, quatre dimensions i els rebuts en brut de cada crida.

## Les regles que fan que els números signifiquin alguna cosa

Cada model s'executa amb el mateix mostreig: temperatura 0.2, top-p 0.95, llavor 42, KV cache q8_0, `--jinja`, un sol slot. Els ajustos estan fixats en dos llocs, els flags del servidor i el cos de la petició, perquè una deriva de configuració al servidor no es coli en una comparació.

Cada model conserva el seu fitxer de perfil. Aquest perfil s'aplica al final i pot sobreescriure la línia base, així que els models competeixen en la seva millor configuració real i no en un muntatge de laboratori que hagi inventat jo. El harness fixa els flags d'infraestructura, i allò amb què va acabar corrent cada model queda registrat a la seva fila de resultat.

Les exclusions s'anoten amb un motiu. Un model que esgota el temps o respon amb prosa on s'esperava un bloc de codi no desapareix en silenci de la mitjana; surt a l'informe, comptat.

El harness només fa servir la biblioteca estàndard de Python. Cap arbre de dependències que es podreixi mentre el benchmark espera.

Cada tasca guarda tres execucions, llavors 42, 43 i 44, i el marcador informa de mitjana ± desviació estàndard. Quan una fila diu `0.84 ±1`, aquesta dispersió forma part de la resposta.

## Què va dir el marcador

El pool actual executa harness v3: 16 tasques d'eines, 60 de codi en quatre llenguatges (32 fàcils, 16 difícils, 12 expertes), 42 tasques d'agent multipas i 32K de context. Les files de sota es van mesurar el 2026-10-13. La part alta de la taula:

| model | eines | codi | agent | velocitat | global |
| --- | --- | --- | --- | --- | --- |
| gemma-4-26b-a4b-it q5_k_xl | 92% | 91% | 93% | 32ms | 0.84 |
| qwen36-35b-distill mxfp4_moe | 92% | 80% | 82% | 17ms | 0.84 |
| qwen3.8-27b turbo q4_k_s | 92% | 84% | 96% | 45ms | 0.81 |
| strata iq3_xxs | 86% | 88% | 96% | 50ms | 0.80 |

Tres coses van destacar.

### Les primeres files són empats

Els dos primers models puntuen 0.84 amb una dispersió de ±1. Dues dècimes separen els quatre primers, ben dins de la seva variància. La puntuació global serveix per ordenar una flota, i no certifica que la primera fila superi la tercera. Qui citi la diferència amb dos decimals està citant soroll.

### El mode thinking va perjudicar

Ho vaig mesurar com una fila separada del pool en lloc de fondre-ho en un sol número. En un banc de 60 tasques de codi amb 11 models, thinking off va excloure 0 de 660 execucions; thinking on en va excloure 14, tretze de fallades de format (una resposta buida, una tanca d'idioma equivocada, prosa on tocava codi) i una per temps esgotat. La latència es va multiplicar: un únic torn de velocitat va passar de 40 a 665 ms. L'execució mediana va gastar 253 tokens de sortida extra pel camí. Per a un agent de codi amb pressupost de tokens, és un impost sense retorn visible.

### Les tasques fàcils de codi no discriminen

Tots els models seriosos van passar les tasques trivials, del 84% al 100%, així que per si sola la dimensió no mesurava res. Se'n van afegir dos nivells: difícil i expert, aquest últim construït amb tasques de depuració de diversos errors amb contractes de sortida estrictes (tornar el fitxer complet corregit, arrodoniment exacte, còpies defensives). El marcador fon els tres nivells en una columna de codi; el desglossament per nivell que registra (`by_level`) és on viu la separació.

## Què et recomanaria fer

Tria per dimensió. Si el teu agent crida eines tot el dia, pondera la columna d'eines. Si edita codi, fes servir el nivell difícil i ignora el fàcil. Si encadena passos, la columna d'agent és el teu número.

Mesura al teu maquinari amb els teus propis perfils. Un quant que va còmode en dues 5080 és una presentació de diapositives en una, i el resultat canvia amb la configuració del KV cache.

Llegeix les exclusions. Un model que falla a l'hora de formatar una crida d'eina de tant en tant no és una mica pitjor que un que sempre l'encerta. En un bucle d'agent, l'atura.

Tracta les files properes com a empats. La meva pròpia taula té quatre models dins d'un punt entre ells. Trio entre ells per velocitat i per com es comporten quan falla una crida, no pel tercer decimal d'una puntuació.

## La lletra petita

Les tasques estan escrites per a aquest harness, les solucions de referència no surten mai de la màquina i els models sota prova són els quants de GPU de consum que la gent executa. Les puntuacions responen a "quin GGUF hauria d'executar per a treball agentic", no a "com n'és de llest aquest model". Mètode complet a `docs/SPEC.md` del repositori.

Marcador i informe en directe: [jordimarsal.github.io/ggufbench](https://jordimarsal.github.io/ggufbench/).
Codi, tasques i rebuts: [github.com/jordimarsal/ggufbench](https://github.com/jordimarsal/ggufbench).
