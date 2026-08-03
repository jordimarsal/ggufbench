ID = "refactor"
LANG = "typescript"
GOAL = "Refactor solution.ts to use more efficient algorithm for fibonacci"
INITIAL_FILES = {"solution.ts": "export function fibonacci(n: number): number {\n    if (n <= 1) return n;\n    return fibonacci(n-1) + fibonacci(n-2);\n}", "test_solution.ts": "import { fibonacci } from './solution';\nif (fibonacci(10) !== 55) throw new Error('fail');\nconsole.log('OK');"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
