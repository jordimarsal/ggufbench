ID = "is_prime"
LANG = "typescript"
PROMPT = "Implementa una funció isPrime(n: number): boolean que retorna true si n és primer, false altrament"
TEST_CODE = "import { isPrime } from './solution';\nif (!isPrime(2)) throw new Error('fail');\nif (!isPrime(3)) throw new Error('fail');\nif (isPrime(4)) throw new Error('fail');\nif (!isPrime(17)) throw new Error('fail');\nif (isPrime(1)) throw new Error('fail');\nconsole.log('OK');"
