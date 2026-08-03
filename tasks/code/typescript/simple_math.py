ID = "simple_math"
LANG = "typescript"
PROMPT = "Implementa una funció add(a: number, b: number): number que retorna a+b"
TEST_CODE = "import { add } from './solution';\nif (add(2,3) !== 5) throw new Error('fail');\nif (add(-1,1) !== 0) throw new Error('fail');\nconsole.log('OK');"