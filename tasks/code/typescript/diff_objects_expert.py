ID = "diff_objects_expert"
LANG = "typescript"
PROMPT = """Implementa diff(a, b): string[] — les diferencies entre dues estructures JSON-like
(objectes plans, arrays i primitius). `a` i `b` son sempre objectes o arrays a l'arrel.

Regles:
- Camins: claus unides per punts i indexos d'array entre claudators (`items[0].name`).
  L'arrel no apareix mai al cami.
- `undefined` = absent (no es un valor); `null` si que es un valor.
- Una entrada per diferencia, amb aquest format exacte:
    `camí: removed`  si el valor hi es a `a` i no a `b`
    `camí: added`    si hi es a `b` i no a `a`
    `camí: changed`  si hi es als dos i son diferents
- Si a i b son objectes, es compara clau a clau; si son arrays, index a index (les llargades
  diferents donen `added`/`removed` a les posicions que sobren).
- Un canvi de TIPUS en un cami (objecte/array vs primitiu, o array vs objecte) compta com una
  sola diferencia d'aquell cami i no s'hi baixa.
- El resultat va ordenat alfabeticament. Si son iguals, llista buida."""
TEST_CODE = """import { diff } from './solution';

function eq(got: string[], expected: string[], label: string) {
  const g = JSON.stringify(got);
  const e = JSON.stringify(expected);
  if (g !== e) throw new Error(label + '\\n--- got:      ' + g + '\\n--- expected: ' + e);
}

eq(diff({ a: 1 }, { a: 1 }), [], 'iguals');
eq(diff({ a: 1 }, { a: 2 }), ['a: changed'], 'canvi de valor');
eq(diff({ a: 1 }, {}), ['a: removed'], 'clau eliminada');
eq(diff({}, { a: 1 }), ['a: added'], 'clau afegida');
eq(diff({ a: { b: 1 } }, { a: { b: 2 } }), ['a.b: changed'], 'anidat');
eq(diff({ a: [1, 2] }, { a: [1, 2, 3] }), ['a[2]: added'], 'array mes llarg');
eq(diff({ a: [1, 2] }, { a: [1] }), ['a[1]: removed'], 'array mes curt');
eq(diff({ a: null }, {}), ['a: removed'], 'null es un valor');
eq(diff({ a: { b: 1 } }, { a: 1 }), ['a: changed'], 'canvi de tipus no baixa');
eq(diff({ a: undefined }, {}), [], 'undefined es absent als dos costats');
eq(diff({}, { a: undefined }), [], 'undefined afegit no compta');
eq(diff({ b: 1, a: { c: 2 } }, { b: 2, a: { c: 3 } }),
   ['a.c: changed', 'b: changed'], 'ordenat');
eq(diff({ items: [{ id: 1, tag: 'x' }] }, { items: [{ id: 1, tag: 'y' }] }),
   ['items[0].tag: changed'], 'objectes dins arrays');
console.log('OK');"""
