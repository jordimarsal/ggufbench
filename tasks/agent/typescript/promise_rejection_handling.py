ID = "promise_rejection_handling"
LANG = "typescript"
GOAL = "Arregla solution.ts perquè passi els tests. Les promeses poden fallar però no es gestionen les rejection."
INITIAL_FILES = {
    "solution.ts": "export async function fetchAll(): Promise<string[]> {\n    const p1 = fetch('/api/users').then(r => r.text());\n    const p2 = fetch('/api/posts').then(r => r.text());\n    return [p1, p2];\n}",
    "test_solution.ts": "import { fetchAll } from './solution';\n(async () => {\n    try {\n        const results = await fetchAll();\n        console.log('OK');\n    } catch (e) {\n        console.log('OK');\n    }\n})();"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
