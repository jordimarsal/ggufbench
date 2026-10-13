ID = "error_union_handling"
LANG = "typescript"
GOAL = "Refactor solution.ts perquè les funcions retornin un discriminated union {ok: T} | {error: string}. Test.ts verifica que cada variant es tracti correctament."
INITIAL_FILES = {
    "solution.ts": "export function parseNumber(input: string): number {\n    const n = Number(input);\n    if (isNaN(n)) return -1;\n    return n;\n}\n\nexport function findUser(id: string, users: { id: string; name: string }[]): { id: string; name: string } | null {\n    return users.find(u => u.id === id) || null;\n}",
    "test_solution.ts": "import { parseNumber, findUser } from './solution';\n// parseNumber returns ok or error\nconst r1 = parseNumber('42');\nif ((r1 as any).ok !== 42) throw new Error('wrong ok value');\nconst r2 = parseNumber('abc');\nif (!(r2 as any).error) throw new Error('should be error');\n// findUser returns ok or error\nconst users = [{ id: 'u1', name: 'Alice' }, { id: 'u2', name: 'Bob' }];\nconst r3 = findUser('u1', users);\nif ((r3 as any).ok?.name !== 'Alice') throw new Error('wrong user');\nconst r4 = findUser('missing', users);\nif (!(r4 as any).error) throw new Error('should be error for missing');\nconsole.log('OK');"
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
