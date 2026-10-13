ID = "async_ordering"
LANG = "typescript"
GOAL = "Arregla solution.ts perquè passi els tests. Les promeses es resoluen fora d'ordre; cal recollir-les en ordre."
INITIAL_FILES = {"solution.ts": "export async function fetchResults(): Promise<string[]> {\n    const p1 = new Promise<string>(resolve => setTimeout(() => resolve('third'), 300));\n    const p2 = new Promise<string>(resolve => setTimeout(() => resolve('first'), 50));\n    const p3 = new Promise<string>(resolve => setTimeout(() => resolve('second'), 150));\n    return [p1, p2, p3];\n}", "test_solution.ts": "import { fetchResults } from './solution';\n(async () => {\n    const results = await fetchResults();\n    if (results[0] !== 'third') throw new Error('wrong order');\n    if (results[1] !== 'first') throw new Error('wrong order');\n    if (results[2] !== 'second') throw new Error('wrong order');\n    console.log('OK');\n})();"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
