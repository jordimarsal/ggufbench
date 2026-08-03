ID = "debug"
LANG = "typescript"
GOAL = "Debug solution.ts - reverseString function is not working correctly"
INITIAL_FILES = {"solution.ts": "export function reverseString(s: string): string {\n    return s;\n}", "test_solution.ts": "import { reverseString } from './solution';\nif (reverseString('abc') !== 'cba') throw new Error('fail');\nconsole.log('OK');"}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
