ID = "async_queue_ordering"
LANG = "typescript"
GOAL = """El sistema de cues processa tasques asíncronament però els resultats tornen en ordre
incorrecte: les promeses es resoluen fora d'ordre i el consumer no pot confiar que la posició
del resultat correspongui a la tasca original.

Punt d'entrada: main(tasks) de solution.ts, retorna un array de {id, value} en l'ordre
original de les tasques. Les tasques tenen delays diferents (50ms, 150ms, 300ms).

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "solution.ts": ('import { enqueue } from "./queue.js";\n'
                    '\n\n'
                    'export async function main(tasks: string[]): Promise<{ id: number; value: string }[]> {\n'
                    '    const results = await enqueue(tasks);\n'
                    '    return results;\n'
                    '}'),
    "worker.ts": ('export async function processTask(id: number, input: string): Promise<string> {\n'
                  '    // Simula treball amb delay aleatori\n'
                  '    const delay = Math.floor(Math.random() * 200) + 50;\n'
                  '    await new Promise(resolve => setTimeout(resolve, delay));\n'
                  '    return `${input}-${id}`;\n'
                  '}'),
    "queue.ts": ('import { processTask } from "./worker.js";\n'
                 '\n\n'
                 'export async function enqueue(tasks: string[]): Promise<{ id: number; value: string }[]> {\n'
                 '    const promises = tasks.map((task, index) =>\n'
                 '        processTask(index, task).then(value => ({ id: index, value }))\n'
                 '    );\n'
                 '    // BUG: retorna les promeses sense esperar-les en ordre\n'
                 '    return promises as any;\n'
                 '}'),
    "logger.ts": ('export function log(msg: string): void {\n'
                  '    console.log(`[${new Date().toISOString()}] ${msg}`);\n'
                  '}'),
    "report.ts": ('import type { Result } from "./types.js";\n'
                  '\n\n'
                  'export function formatReport(results: Result[]): string {\n'
                  '    return results.map(r => `T${r.id}: ${r.value}`).join("\\n");\n'
                  '}'),
    "types.ts": ('export interface Result {\n'
                 '    id: number;\n'
                 '    value: string;\n'
                 '}'),
    "test_solution.ts": ('import { main } from "./solution.js";\n'
                         '\n\n'
                         '(async () => {\n'
                         '    const tasks = ["alpha", "beta", "gamma"];\n'
                         '    const results = await main(tasks);\n'
                         '\n'
                         '    if (results.length !== 3) throw new Error("wrong count");\n'
                         '    if (results[0].id !== 0) throw new Error("wrong order at 0");\n'
                         '    if (results[1].id !== 1) throw new Error("wrong order at 1");\n'
                         '    if (results[2].id !== 2) throw new Error("wrong order at 2");\n'
                         '\n'
                         '    // Els valors han de ser deterministes, no aleatoris\n'
                         '    if (!results[0].value.startsWith("alpha-")) throw new Error("bad alpha");\n'
                         '    if (!results[1].value.startsWith("beta-")) throw new Error("bad beta");\n'
                         '    if (!results[2].value.startsWith("gamma-")) throw new Error("bad gamma");\n'
                         '\n'
                         '    console.log("OK");\n'
                         '})();'),
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 14
