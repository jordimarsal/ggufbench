ID = "mapped_type_refactor"
LANG = "typescript"
GOAL = "Refactor solution.ts i utils.ts per usar mapped types. solution.ts defineix User; utils.ts ha de generar ReadonlyUser amb mapped type."
INITIAL_FILES = {
    "solution.ts": "export interface User {\n    name: string;\n    email: string;\n    age: number;\n}\n\nexport function createUser(name: string, email: string, age: number): User {\n    return { name, email, age };\n}",
    "utils.ts": "export type ReadonlyUser = {\n    readonly name: string;\n    readonly email: string;\n    readonly age: number;\n};\n\nexport function makeReadonly(user: User): ReadonlyUser {\n    return { ...user } as ReadonlyUser;\n}"
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
