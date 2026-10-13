ID = "namespace_to_module"
LANG = "typescript"
GOAL = "Migra solution.ts i utils.ts de namespaces a ES modules. Test.ts importa les funcions amb import/export estàndard."
INITIAL_FILES = {
    "solution.ts": "export namespace App {\n    export function greet(name: string): string {\n        return `Hello, ${name}!`;\n    }\n\n    export function farewell(name: string): string {\n        return `Goodbye, ${name}!`;\n    }\n}",
    "utils.ts": "export namespace Utils {\n    export function capitalize(s: string): string {\n        if (!s) return s;\n        return s.charAt(0).toUpperCase() + s.slice(1);\n    }\n\n    export function repeat(s: string, n: number): string {\n        return s.repeat(n);\n    }\n}",
    "test_solution.ts": "import { greet, farewell } from './solution';\nimport { capitalize, repeat } from './utils';\nif (greet('Alice') !== 'Hello, Alice!') throw new Error('wrong greet');\nif (farewell('Bob') !== 'Goodbye, Bob!') throw new Error('wrong farewell');\nif (capitalize('alice') !== 'Alice') throw new Error('wrong capitalize');\nif (repeat('ha', 3) !== 'hahaha') throw new Error('wrong repeat');\nconsole.log('OK');"
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
