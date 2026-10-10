ID = "vault_engine_expert"
LANG = "python"
PROMPT = """Implementa la classe Vault: un diposit clau->valor amb operacions atomiques.

Metodes:
- set(key, value): emmagatzema (sobreescriu si existeix).
- get(key): retorna el valor o None si no existeix.
- delete(key): retorna True si existia (i l'esborra), False si no.
- compare_and_set(key, expected, new): si el valor actual es `expected`, posa `new`
  i retorna True; si no, no toca res i retorna False. Si la clau NO existeix, l'valor
  actual es considera None (aixi compare_and_set(k, None, v) crea la clau).
- keys_with_prefix(prefix): llista de les claus que comencen per `prefix`, ordenades
  lexicograficament. Una clau que es igual al prefix tambe hi es.
- apply_batch(ops): `ops` es una llista de tuples, en ordre:
  ("set", k, v) | ("delete", k) | ("cas", k, old, new)
  Les operacions s'apliquen sequencialment sobre una COPIA de l'estat; si alguna
  operacio es invalida en el moment en que toca (un cas amb valor actual diferent
  de `old`, o un delete d'una clau que no existeix) es DESCARTA la copia sencera
  (rollback) i retorna -1. Si totes son valides, la copia substitueix l'estat i
  retorna el nombre d'operacions aplicades. Un ("set", ...) mai es invalid."""
TEST_CODE = """from solution import *
v = Vault()
v.set('a', 1)
assert v.get('a') == 1
assert v.get('no') is None
assert v.delete('a') is True
assert v.delete('a') is False
assert v.get('a') is None
v.set('x', 10)
assert v.compare_and_set('x', 10, 20) is True
assert v.get('x') == 20
assert v.compare_and_set('x', 10, 30) is False
assert v.get('x') == 20
assert v.compare_and_set('x', None, 1) is False
assert v.get('x') == 20
assert v.compare_and_set('y', None, 5) is True
assert v.get('y') == 5
v.set('ab', 1); v.set('az', 2); v.set('ba', 3); v.set('a', 0)
assert v.keys_with_prefix('a') == ['a', 'ab', 'az'], v.keys_with_prefix('a')
assert v.keys_with_prefix('az') == ['az']
assert v.keys_with_prefix('zz') == []
b = Vault()
b.set('k', 1)
n = b.apply_batch([('set', 'k', 2), ('set', 'm', 3)])
assert n == 2 and b.get('k') == 2 and b.get('m') == 3
n = b.apply_batch([('set', 'k', 99), ('cas', 'k', 1, 2)])
assert n == -1, n
assert b.get('k') == 2 and b.get('m') == 3, 'rollback incomplet'
n = b.apply_batch([('set', 'q', 1), ('delete', 'missing')])
assert n == -1 and b.get('q') is None, 'rollback incomplet (q)'
assert b.apply_batch([]) == 0
print('OK')"""
