ID = "fibonacci"
LANG = "typescript"
PROMPT = "Implementa una funció fibonacci(n: number): number que retorna l'n-èssim número de Fibonacci"
TEST_CODE = "import { fibonacci } from './solution';\nif (fibonacci(0) !== 0) throw new Error('fail');\nif (fibonacci(1) !== 1) throw new Error('fail');\nif (fibonacci(10) !== 55) throw new Error('fail');\nconsole.log('OK');"
