ID = "count_words"
LANG = "typescript"
PROMPT = "Implementa una funció countWords(s: string): number que retorna el nombre de paraules"
TEST_CODE = "import { countWords } from './solution';\nif (countWords('hello world') !== 2) throw new Error('fail');\nif (countWords('a b c d') !== 4) throw new Error('fail');\nif (countWords('') !== 0) throw new Error('fail');\nconsole.log('OK');"
