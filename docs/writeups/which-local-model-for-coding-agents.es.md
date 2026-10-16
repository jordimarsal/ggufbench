# ¿Qué modelo local debería ejecutar un agente de código? Seis GGUFs y un motor Strata, un harness, recibos

*También disponible en [inglés](which-local-model-for-coding-agents.md) y [catalán](which-local-model-for-coding-agents.ca.md).*

Ejecuto agentes de código en mi propio hardware. llama.cpp en dos RTX 5080, modelos de mi carpeta `models`, y una pregunta: ¿qué GGUF, en qué quant, debo cargar antes de ponerme a trabajar?

Los leaderboards públicos miden otra cosa. En su mayoría, los modelos están entrenados sobre ellos, puntúan respuestas de un solo disparo y no dicen nada sobre si un modelo sabe llamar a una herramienta con argumentos bien formados, sobrevivir a un bucle de varias llamadas, leer una carpeta, editar un archivo y verificar su propio cambio. Esa es la faena que hace un agente todo el día, así que dejé de leer esas tablas para esta decisión y construí [ggufbench](https://github.com/jordimp/ggufbench).

Un harness, las mismas condiciones, cuatro dimensiones y los recibos en bruto de cada llamada — esta ronda, seis GGUFs bajo llama.cpp y un modelo bajo el motor [Strata](https://github.com/Niko1221/Strata), cada uno en los dos modos de thinking.

## Las reglas que hacen que los números signifiquen algo

Cada modelo se ejecuta con el mismo muestreo: temperatura 0.2, top-p 0.95, top-k 40, min-p 0.05, semilla 42, KV cache q8_0, `--jinja`, un solo slot. Cada valor del muestreo está fijado explícitamente, porque un GGUF lleva su propia metadata de muestreo — esta flota sola embarca tres valores distintos de `top_k` (20, 64 y ninguno) — y un valor no fijado no es una condición compartida sino una por modelo. Los ajustes están fijados en dos sitios, los flags del servidor y el cuerpo de la petición, para que una deriva de configuración en el servidor no se cuele en una comparación.

Cada modelo conserva su archivo de perfil. Ese perfil se aplica al final y puede sobrescribir la línea base, así que los modelos compiten en su mejor configuración real y no en un montaje de laboratorio que haya inventado yo. El harness fija los flags de infraestructura, y aquello con lo que acabó corriendo cada modelo queda registrado en su fila de resultado.

Las exclusiones se anotan con un motivo. Un modelo que agota el tiempo o responde con prosa donde se esperaba un bloque de código no desaparece en silencio de la media; aparece en el informe, contado.

El harness solo usa la biblioteca estándar de Python. Ningún árbol de dependencias que se pudra mientras el benchmark espera.

Cada tarea guarda tres ejecuciones, semillas 42, 43 y 44, y el marcador informa de media ± desviación estándar. Cuando una fila dice `0.85 ±1`, esa dispersión forma parte de la respuesta.

## Lo que dijo el marcador

El pool actual ejecuta el conjunto v5: 18 tareas de herramientas, 72 de código en cuatro lenguajes (32 fáciles, 20 difíciles, 20 expertas), 72 tareas de agente multipaso (13 de ellas proyectos de varios archivos) y 32K de presupuesto de salida para el código. Las filas de abajo se midieron la noche del 2026-10-14/15. La parte alta de la tabla:

| modelo | think | herramientas | código | agente | velocidad | global |
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

*★ = el modo thinking óptimo de cada modelo según los datos: calidad dentro de ±0.02 del otro modo y sin más tiempo de reloj; los empates exactos van a off.*

Tres cosas destacaron.

### Las primeras filas son empates

Las diez primeras filas abarcan cinco centésimas — de 0.85 a 0.80 — y las filas vecinas quedan como máximo a una o dos centésimas, del mismo tamaño que la dispersión entre tiradas que acompaña a cada puntuación. La puntuación global ordena una flota; no certifica que la fila 1 supere a la 7. Quien ordene dos filas cercanas por su segundo decimal está citando ruido.

### El modo thinking es un impuesto que solo paga en el código difícil

Lo medí como filas separadas en lugar de fundirlo en un solo número. Thinking on multiplica la latencia por turno — cada fila on excepto la del MiniCPM corre entre 280 y 1060 ms contra los 19–85 ms de off (la on del MiniCPM aterriza en 23 ms) — y también cuesta calidad en todos los modelos, con el MiniCPM como único empate. Además, concentra las exclusiones: de las 1.512 ejecuciones de código de la flota por modo, off excluye 6 y on excluye 101, la mayoría respuestas sin bloque de código donde se esperaba uno (tareas completamente excluidas: 2 contra 14).

Donde sí compra algo es en el nivel difícil de código: el UD-Q3 sube del 79% al 93% en el código global (92% difícil, 91% experto), el Ornith +10 puntos sobre su propio off, el Strata +6, el Heretic +4 — y el bucle de agente del Heretic llega al 97%, el mejor de la flota. En las tareas que lo necesitan, el thinking vale diez veces la espera; en el resto, es un impuesto sin retorno visible.

### Las tareas fáciles de código no discriminan

Con thinking off, toda la flota aterriza entre el 91% y el 100% en el nivel fácil, mientras que difícil y experto viven entre el 47% y el 87%. La separación está en esos dos niveles — sobre todo en las expertas, construidas con depuración de varios errores y contratos de salida estrictos (devolver el archivo completo corregido, redondeo exacto, copias defensivas). El marcador funde los tres niveles en una columna de código; el desglose por nivel que registra (`by_level`) es donde vive la discusión.

## Lo que te recomendaría hacer

Elige por dimensión. En esta tabla, las herramientas son del MiniCPM (100%), el código difícil del UD-Q3 con thinking (92% difícil, 91% experto), el bucle de agente del Heretic con thinking (97%) y la velocidad por turno del qwen36 off (19 ms). Ninguna fila lo gana todo.

Mide en tu propio hardware con tus propios perfiles. Un quant que va cómodo en dos 5080 es una presentación de diapositivas en una, y el resultado cambia con la configuración del KV cache.

Lee las exclusiones. Un modelo que falla al formatear una llamada de herramienta de vez en cuando no es un poco peor que otro que siempre acierta. En un bucle de agente, lo detiene.

Trata las filas cercanas como empates. Diez filas dentro de cinco centésimas no son una clasificación, son un grupo. Elijo dentro de él por latencia y por cómo se comporta un modelo cuando falla una llamada, no por el tercer decimal de una puntuación.

## La letra pequeña

Las tareas están escritas para este harness, las soluciones de referencia no salen nunca de la máquina y los modelos bajo prueba son los quants de GPU de consumo que la gente ejecuta. Las puntuaciones responden a "qué GGUF debería ejecutar para trabajo agéntico", no a "cuán listo es este modelo". Dos filas thinking-on (gemma, strata) se midieron con límites de llamadas más estrechos que el resto y el informe las marca como pendientes de una pasada justa; los trece modelos retirados por el camino viven en su pestaña Retired, solo registro. Método completo en `docs/SPEC.md` del repositorio.

Marcador e informe en vivo: [jordimp.github.io/ggufbench](https://jordimp.github.io/ggufbench/).
Código, tareas y recibos: [github.com/jordimp/ggufbench](https://github.com/jordimp/ggufbench).
