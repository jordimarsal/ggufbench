ID = "jsonl_agg_expert"
LANG = "typescript"
PROMPT = """Implementa la funcio exportada

    export function process(path: string):
      { valid: number; invalid: number; total: number; kinds: string[] }

que resumeix el fitxer `events.jsonl` (a la feina de test; l'hauras de processar
en temps d'execucio, no el pots veure ara). Regles, linia a linia:
- Linies buides o que comencen per `#` (despres d'espais): es salten.
- La resta ha de ser JSON estricte i un objecte (JSON.parse; les comes extra al
  final NO son JSON valid): qualsevol altra cosa es INVALIDA.
- Un objecte es valid si te `kind` igual a "click", "view" o "error" I `n` un
  enter >= 0 (no decimal, no negatiu). Qualsevol altra cosa es INVALIDA.
- Invalides: es compten i es descarten (no afecten total ni kinds).
- total = suma del `n` dels valides; kinds = els `kind` dels valides, sense
  duplicats i ordenats lexicograficament.
El nom del camp i els valors de l'enum son sensibles a majuscules i exactes."""
TEST_CODE = """import { process } from './solution';

const r = process('events.jsonl');
if (r.valid !== 6) throw new Error('valid -> 6, va ' + r.valid);
if (r.invalid !== 6) throw new Error('invalid -> 6, va ' + r.invalid);
if (r.total !== 33) throw new Error('total -> 33, va ' + r.total);
if (JSON.stringify(r.kinds) !== JSON.stringify(['click', 'error', 'view']))
  throw new Error('kinds: ' + JSON.stringify(r.kinds));
console.log('OK');"""
EXTRA_FILES = {"events.jsonl": """# esdeveniments prod 2026-09
{"kind":"click","n":3}
{"kind":"view","n":10}
{"kind":"error","n":1}

{"kind":"click","n":2}
{"kind":"click","n":-5}
{"kind":"save","n":4}
{"kind":"view","n":2.5}
not json at all
{"kind":"click"}
{"kind":"error","n":7,}
{"kind":"view","n":12}
{"kind": "click", "n" : 5}
"""}
