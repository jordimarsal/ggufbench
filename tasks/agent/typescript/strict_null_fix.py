ID = "strict_null_fix"
LANG = "typescript"
GOAL = "Arregla solution.ts perquè passi els tests. La funció getFullName no gestiona les propietats opcionals."
INITIAL_FILES = {
    "solution.ts": "export interface User {\n    firstName?: string;\n    lastName?: string;\n}\n\nexport function getFullName(user: User): string {\n    return user.firstName + ' ' + user.lastName;\n}",
    "test_solution.ts": "import { getFullName } from './solution';\nif (getFullName({ firstName: 'Alice', lastName: 'Smith' }) !== 'Alice Smith') throw new Error('wrong');\nif (getFullName({ lastName: 'Smith' }) !== 'Smith') throw new Error('wrong');\nconsole.log('OK')"
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
