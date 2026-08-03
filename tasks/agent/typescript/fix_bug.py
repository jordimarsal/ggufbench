ID = "fix_bug"
LANG = "typescript"
GOAL = "Fix the bug in solution.ts - add function should return sum, not difference"
INITIAL_FILES = {"solution.ts": "export function add(a: number, b: number): number {\n    return a - b;\n}", "test_solution.ts": "import { add } from './solution';\nif (add(2,3) !== 5) throw new Error('fail');\nconsole.log('OK');"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
