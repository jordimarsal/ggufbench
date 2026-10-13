ID = "readonly_deep_refactor"
LANG = "typescript"
GOAL = "Refactor solution.ts perquè l'objecte retornat per createUser sigui immutable de forma profunda (deep freeze): ni l'usuari ni la seva adreça es poden modificar en runtime. El test verifica amb Object.isFrozen i que les mutacions no tinguin efecte."
INITIAL_FILES = {
    "solution.ts": "export interface User {\n    name: string;\n    email: string;\n    address: {\n        street: string;\n        city: string;\n        zip: string;\n    };\n}\n\nexport function createUser(name: string, email: string, street: string, city: string, zip: string): User {\n    return {\n        name,\n        email,\n        address: { street, city, zip },\n    };\n}",
    "test_solution.ts": "import { User, createUser } from './solution';\nconst u: User = createUser('Alice', 'alice@example.com', 'Carrer Major 1', 'Barcelona', '08001');\nif (u.name !== 'Alice') throw new Error('wrong name');\nif (!Object.isFrozen(u)) throw new Error('user not frozen');\nif (!Object.isFrozen(u.address)) throw new Error('address not frozen');\nconst before = (u as any).name;\nconst beforeCity = (u as any).address.city;\ntry { (u as any).name = 'Bob'; } catch {}\ntry { (u as any).address.city = 'Madrid'; } catch {}\nif ((u as any).name !== before) throw new Error('mutation took effect');\nif ((u as any).address.city !== beforeCity) throw new Error('nested mutation took effect');\nconsole.log('OK');"
}
TEST_FILE = "test_solution.ts"
MAX_TURNS = 8
