ID = "bubble_sort"
LANG = "typescript"
PROMPT = "Implementa una funció bubbleSort(arr: number[]): number[] que retorna l'array ordenat"
TEST_CODE = "import { bubbleSort } from './solution';\nconst r1 = bubbleSort([3,1,2]);\nif (r1.length !== 3 || r1[0] !== 1 || r1[1] !== 2 || r1[2] !== 3) throw new Error('fail');\nconst r2 = bubbleSort([]);\nif (r2.length !== 0) throw new Error('fail');\nconsole.log('OK');"
