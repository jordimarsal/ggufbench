# ¿Qué modelo local debería ejecutar un agente de código? Nueve GGUFs, un harness, recibos

*También disponible en [inglés](which-local-model-for-coding-agents.md) y [catalán](which-local-model-for-coding-agents.ca.md).*

Ejecuto agentes de código en mi propio hardware. llama.cpp en dos RTX 5080, modelos de mi carpeta `models`, y una pregunta: ¿qué GGUF, en qué quant, debo cargar antes de ponerme a trabajar?

Los leaderboards públicos miden otra cosa. En su mayoría, los modelos están entrenados sobre ellos, puntúan respuestas de un solo disparo y no dicen nada sobre si un modelo sabe llamar a una herramienta con argumentos bien formados, sobrevivir a un bucle de varias llamadas, leer una carpeta, editar un archivo y verificar su propio cambio. Esa es la faena que hace un agente todo el día, así que dejé de leer esas tablas para esta decisión y construí [ggufbench](https://github.com/jordimarsal/ggufbench).

Un harness, las mismas condiciones, cuatro dimensiones y los recibos en bruto de cada llamada.

## Las reglas que hacen que los números signifiquen algo

Cada modelo se ejecuta con el mismo muestreo: temperatura 0.2, top-p 0.95, semilla 42, KV cache q8_0, `--jinja`, un solo slot. Los ajustes están fijados en dos sitios, los flags del servidor y el cuerpo de la petición, para que una deriva de configuración en el servidor no se cuele en una comparación.

Cada modelo conserva su archivo de perfil. Ese perfil se aplica al final y puede sobrescribir la línea base, así que los modelos compiten en su mejor configuración real y no en un montaje de laboratorio que haya inventado yo. El harness fija los flags de infraestructura, y aquello con lo que acabó corriendo cada modelo queda registrado en su fila de resultado.

Las exclusiones se anotan con un motivo. Un modelo que agota el tiempo o responde con prosa donde se esperaba un bloque de código no desaparece en silencio de la media; aparece en el informe, contado.

El harness solo usa la biblioteca estándar de Python. Ningún árbol de dependencias que se pudra mientras el benchmark espera.

Cada tarea guarda tres ejecuciones, semillas 42, 43 y 44, y el marcador informa de media ± desviación estándar. Cuando una fila dice `0.84 ±1`, esa dispersión forma parte de la respuesta.

## Lo que dijo el marcador

El pool actual ejecuta harness v3: 16 tareas de herramientas, 60 de código en cuatro lenguajes (32 fáciles, 16 difíciles, 12 expertas), 42 tareas de agente multipaso y 32K de contexto. Las filas de abajo se midieron el 2026-10-13. La parte alta de la tabla:

| modelo | herramientas | código | agente | velocidad | global |
| --- | --- | --- | --- | --- | --- |
| gemma-4-26b-a4b-it q5_k_xl | 92% | 91% | 93% | 32ms | 0.84 |
| qwen36-35b-distill mxfp4_moe | 92% | 80% | 82% | 17ms | 0.84 |
| qwen3.8-27b turbo q4_k_s | 92% | 84% | 96% | 45ms | 0.81 |
| strata iq3_xxs | 86% | 88% | 96% | 50ms | 0.80 |

Tres cosas destacaron.

### Las primeras filas son empates

Los dos primeros modelos puntúan 0.84 con una dispersión de ±1. Dos décimas separan a los cuatro primeros, muy dentro de su varianza. La puntuación global sirve para ordenar una flota, y no certifica que la primera fila supere a la tercera. Quien cite la diferencia con dos decimales está citando ruido.

### El modo thinking perjudicó

Lo medí como una fila separada del pool en lugar de fundirlo en un solo número. En un banco de 60 tareas de código con 11 modelos, thinking off excluyó 0 de 660 ejecuciones; thinking on excluyó 14, trece de ellas fallos de formato (una respuesta vacía, una cerca de lenguaje equivocado, prosa donde tocaba código) y una por tiempo agotado. La latencia se multiplicó: un único turno de velocidad pasó de 40 a 665 ms. La ejecución mediana gastó 253 tokens de salida extra por el camino. Para un agente de código con presupuesto de tokens, es un impuesto sin retorno visible.

### Las tareas fáciles de código no discriminan

Todos los modelos serios pasaron las tareas triviales, del 84% al 100%, así que por sí sola la dimensión no medía nada. Se añadieron dos niveles: difícil y experto, este último construido con tareas de depuración de varios errores con contratos de salida estrictos (devolver el archivo completo corregido, redondeo exacto, copias defensivas). El marcador funde los tres niveles en una columna de código; el desglose por nivel que registra (`by_level`) es donde vive la separación.

## Lo que te recomendaría hacer

Elige por dimensión. Si tu agente llama a herramientas todo el día, pondera la columna de herramientas. Si edita código, usa el nivel difícil e ignora el fácil. Si encadena pasos, la columna de agente es tu número.

Mide en tu propio hardware con tus propios perfiles. Un quant que va cómodo en dos 5080 es una presentación de diapositivas en una, y el resultado cambia con la configuración del KV cache.

Lee las exclusiones. Un modelo que falla al formatear una llamada de herramienta de vez en cuando no es un poco peor que otro que siempre acierta. En un bucle de agente, lo detiene.

Trata las filas cercanas como empates. Mi propia tabla tiene cuatro modelos a un punto entre ellos. Elijo entre ellos por velocidad y por cómo se comportan cuando falla una llamada, no por el tercer decimal de una puntuación.

## La letra pequeña

Las tareas están escritas para este harness, las soluciones de referencia no salen nunca de la máquina y los modelos bajo prueba son los quants de GPU de consumo que la gente ejecuta. Las puntuaciones responden a "qué GGUF debería ejecutar para trabajo agéntico", no a "cuán listo es este modelo". Método completo en `docs/SPEC.md` del repositorio.

Marcador e informe en vivo: [jordimarsal.github.io/ggufbench](https://jordimarsal.github.io/ggufbench/).
Código, tareas y recibos: [github.com/jordimarsal/ggufbench](https://github.com/jordimarsal/ggufbench).
