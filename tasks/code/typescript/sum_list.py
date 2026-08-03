ID = "sum_list"
LANG = "typescript"
PROMPT = "Implementa una funció sumList(arr: number[]): number que retorna la suma dels elements"
TEST_CODE = "import { sumList } from './solution';\nif (sumList([1,2,3]) !== 6) throw new Error('fail');\nif (sumList([-1,0,1]) !== 0) throw new Error('fail');\nif (sumList([]) !== 0) throw new Error('fail');\nconsole.log('OK');"
