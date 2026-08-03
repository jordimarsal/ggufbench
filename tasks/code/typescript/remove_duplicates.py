ID = "remove_duplicates"
LANG = "typescript"
PROMPT = "Implementa una funció removeDuplicates(arr: T[]): T[] que retorna una nova array sense duplicats"
TEST_CODE = "import { removeDuplicates } from './solution';\nconst r1 = removeDuplicates([1,2,2,3]);\nif (r1.length !== 3 || r1[0] !== 1 || r1[1] !== 2 || r1[2] !== 3) throw new Error('fail');\nconst r2 = removeDuplicates([]);\nif (r2.length !== 0) throw new Error('fail');\nconsole.log('OK');"
