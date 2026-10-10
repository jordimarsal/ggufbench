ID = "proc_registry_expert"
LANG = "typescript"
PROMPT = """Implementa la classe Registry<T> (exportada) — un registre amb dependències per
resoldre components de forma perezosa.

- new Registry<T>() — buit.
- register(name: string, deps: string[], factory: () => T): void
  * llança Error si el nom ja esta registrat (missatge que contingui 'duplicate')
  * llança Error si deps conte el mateix name (missatge amb 'self')
  * les deps poden referir-se a noms que encara no s'han registrat (es comprova
    a resolve)
- resolve(name: string): T
  * llança Error si el nom es desconegut ('unknown')
  * resol PRIMER les dependències (en l'ordre donat) i despres crida factory
  * detecta cicles ('cycle') i llança en lloc de penjar-se
  * MEMOITZA: cada factory es crida COM A MOLT UN VEZ per nom; tots els que
    depenen d'aquell nom reben la MATEIXA instància (identitat compartida)
- size(): number — noms registrats."""
TEST_CODE = """import { Registry } from './solution';

const r = new Registry<string>();
let calls = 0;
r.register('base', [], () => { calls++; return 'B'; });
r.register('mid', ['base'], () => 'M:' + r.resolve('base'));
r.register('top', ['mid', 'base'], () => 'T:' + r.resolve('mid'));
const t1 = r.resolve('top');
if (t1 !== 'T:M:B') throw new Error('ordre de construccio: ' + t1);
if (calls !== 1) throw new Error('base construida una vegada, va ' + calls);
const b = r.resolve('base');
if (b !== 'B') throw new Error('memo');
if (calls !== 1) throw new Error('sense re-construccio, va ' + calls);
r.register('left', ['base'], () => 'L:' + r.resolve('base'));
r.register('right', ['base'], () => 'R:' + r.resolve('base'));
r.resolve('left');
r.resolve('right');
if (calls !== 1) throw new Error('instancia compartida, va ' + calls);
if (r.resolve('top') !== t1) throw new Error('top estable');
if (r.size() !== 5) throw new Error('size -> 5, va ' + r.size());
let threw = false;
try { r.register('base', [], () => 'x'); } catch { threw = true; }
if (!threw) throw new Error('duplicate ha de llencar');
threw = false;
try { r.register('selfy', ['selfy'], () => 'S'); } catch { threw = true; }
if (!threw) throw new Error('self dep ha de llencar');
threw = false;
try { r.resolve('nope'); } catch { threw = true; }
if (!threw) throw new Error('unknown ha de llencar');
r.register('c1', ['c2'], () => 'C1');
r.register('c2', ['c1'], () => 'C2');
threw = false;
try { r.resolve('c1'); } catch { threw = true; }
if (!threw) throw new Error('cicle ha de llencar');
console.log('OK');"""
