ID = "event_debug_expert"
LANG = "typescript"
PROMPT = """Aquesta classe de log rotatiu te 3 errors subtils. Corregeix-los TORNANT EL
FITXER COMPLET (mateixa API). Contracte del fitxer corregit:
- new RollingLog(max): reté COM A MOLT `max` linies (les mes recents).
- push(line): afegeix i retalla.
- lines(): copia DEFENSIVA — mutar el resultat NO pot tocar l'estat intern.
- stats(): {INFO, WARN, ERR} = comptes de linies que comencen per cada prefix.
  Ha de funcionar amb els prefixes indicats i els tres mesures simultaniament.

```ts
export class RollingLog {
  private max: number;
  private data: string[] = [];

  constructor(max: number) {
    this.max = max;
  }

  push(line: string): void {
    this.data.push(line);
    while (this.data.length > this.max + 1) this.data.shift();
  }

  lines(): string[] {
    return this.data;
  }

  private countPrefix(prefix: string): number {
    return this.data.filter((l) => l.startsWith(prefix)).length;
  }

  stats(): Record<string, number> {
    const counter = this.countPrefix;
    return { INFO: counter('INFO'), WARN: counter('WARN'), ERR: counter('ERR') };
  }
}
```"""
TEST_CODE = """import { RollingLog } from './solution';

const l = new RollingLog(3);
l.push('INFO a');
l.push('WARN b');
l.push('ERR c');
const s = l.stats();
if (s.INFO !== 1 || s.WARN !== 1 || s.ERR !== 1)
  throw new Error('stats: ' + JSON.stringify(s));
l.push('INFO d');
const lines = l.lines();
if (lines.length !== 3) throw new Error('retencio max=3, va ' + lines.length);
lines.push('POISON');
if (l.lines().length !== 3) throw new Error('lines ha de ser copia defensiva');
const l2 = new RollingLog(1);
l2.push('x');
l2.push('y');
if (l2.lines().length !== 1) throw new Error('max=1, va ' + l2.lines().length);
if (l2.lines()[0] !== 'y') throw new Error('la mes recent es la y');
const s2 = l2.stats();
if (s2.INFO !== 0 || s2.WARN !== 0 || s2.ERR !== 0)
  throw new Error('stats buides: ' + JSON.stringify(s2));
console.log('OK');"""
