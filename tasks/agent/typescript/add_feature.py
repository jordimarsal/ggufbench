ID = "add_feature"
LANG = "typescript"
GOAL = "Add a multiply function to solution.ts"
INITIAL_FILES = {"solution.ts": "export function add(a: number, b: number): number {\n    return a + b;\n}", "test_solution.ts": "import { add, multiply } from './solution';\nif (add(2,3) !== 5) throw new Error('fail');\nif (multiply(2,3) !== 6) throw new Error('fail');\nconsole.log('OK');"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
