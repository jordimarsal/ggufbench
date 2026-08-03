ID = "optimize"
LANG = "typescript"
GOAL = "Optimize solution.ts to use more efficient approach for isPrime"
INITIAL_FILES = {"solution.ts": "export function isPrime(n: number): boolean {\n    for (let i = 2; i < n; i++) {\n        if (n % i === 0) return false;\n    }\n    return n > 1;\n}", "test_solution.ts": "import { isPrime } from './solution';\nif (!isPrime(17)) throw new Error('fail');\nconsole.log('OK');"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
