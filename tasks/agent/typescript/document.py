ID = "document"
LANG = "typescript"
GOAL = "Add JSDoc comments to all functions in solution.ts"
INITIAL_FILES = {"solution.ts": "export function add(a: number, b: number): number {\n    return a + b;\n}\nexport function subtract(a: number, b: number): number {\n    return a - b;\n}", "test_solution.ts": "import { add, subtract } from './solution';\nif (add(2,3) !== 5) throw new Error('fail');\nif (subtract(5,2) !== 3) throw new Error('fail');\nconsole.log('OK');"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
