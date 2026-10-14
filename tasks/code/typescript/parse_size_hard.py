ID = "parse_size_hard"
LANG = "typescript"
PROMPT = """Implementa parseSize(text: string): number que retorni la mida en bytes, amb aquestes
regles:

- Numero decimal estricte, sense signe, amb com a maxim un punt decimal i com a minim un
  digit abans i despres del punt si el punt hi es ("0", "512", "1.5" si; ".5", "1.", "1.2.3",
  "-1", "" no).
- Sufix d'unitat opcional insensible a majuscules, amb una "B" final opcional i equivalent:
  K/KB = 1000, M/MB = 1000^2, G/GB = 1000^3, T/TB = 1000^4.
- Espais al principi i al final permesos, i com a maxim un espai entre el numero i la unitat
  (" 4 Gb " es valid).
- Qualsevol altra entrada ha de llançar un Error.
- Si el decimal no es exacte es trunca cap a baix ("1.0005K" -> 1000)."""
TEST_CODE = """import { parseSize } from './solution';
if (parseSize('0') !== 0) throw new Error('fail 0');
if (parseSize('512') !== 512) throw new Error('fail 512');
if (parseSize('1K') !== 1000) throw new Error('fail 1K');
if (parseSize('1k') !== 1000) throw new Error('fail 1k');
if (parseSize('1KB') !== 1000) throw new Error('fail 1KB');
if (parseSize('1.5K') !== 1500) throw new Error('fail 1.5K');
if (parseSize('2.5M') !== 2500000) throw new Error('fail 2.5M');
if (parseSize('3G') !== 3000000000) throw new Error('fail 3G');
if (parseSize('1T') !== 1000000000000) throw new Error('fail 1T');
if (parseSize(' 4 Gb ') !== 4000000000) throw new Error('fail 4 Gb');
if (parseSize('1.0005K') !== 1000) throw new Error('fail trunc');
const bad = ['', '   ', 'K', 'KB', '1X', '1.2.3K', '-1', '.5K', '1.K', '1Kb2', '1 K K', '1 2K'];
for (const b of bad) {
  let threw = false;
  try { parseSize(b); } catch { threw = true; }
  if (!threw) throw new Error('hauria de fallar: [' + b + ']');
}
console.log('OK');"""
