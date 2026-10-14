ID = "ttl_cache_debug_expert"
LANG = "python"
PROMPT = """El modul de cache seguent te 2 errors subtils i no sabem quins son.
Corregeix-los TORNANT EL FITXER COMPLET (mateixa API, sense treure metodes).

Contracte que ha de complir el modul corregit:
- `capacity`: com a molt `capacity` entrades vives; en inserir amb la cache plena s'expulsa
  la MENYS RECENTMENT USADA (un `get` encertat compta com a ús).
- `ttl`: una entrada es valida mentre `edat < ttl`; amb `edat == ttl` ja ha caducat (get
  retorna None i l'elimina). `tick(n)` avança el rellotge.
- `keys()` retorna les claus vives de mes recent a menys recent.
- `_purge()` elimina les caducades; `get` retorna None per a claus absents o caducades.

```python
class TTLCache:
    \"\"\"Cache amb caducitat i capacitat, amb rellotge injectable (determinista).\"\"\"

    def __init__(self, capacity=3, ttl=10):
        self.capacity = capacity
        self.ttl = ttl
        self._t = 0
        self._data = {}          # key -> [value, stamp]

    def tick(self, n=1):
        \"\"\"Avenca el rellotge n unitats i retorna el temps actual.\"\"\"
        self._t += n
        return self._t

    def put(self, key, value):
        self._data[key] = [value, self._t]
        self._purge()
        while len(self._data) > self.capacity:
            lru = min(self._data, key=lambda k: self._data[k][1])
            del self._data[lru]

    def get(self, key):
        entry = self._data.get(key)
        if entry is None:
            return None
        if self._t - entry[1] > self.ttl:
            del self._data[key]
            return None
        return entry[0]

    def _purge(self):
        for k in [k for k, e in self._data.items() if self._t - e[1] > self.ttl]:
            del self._data[k]

    def keys(self):
        \"\"\"Claus vives de mes recent a menys recent.\"\"\"
        self._purge()
        return sorted(self._data, key=lambda k: self._data[k][1], reverse=True)
```
"""
TEST_CODE = """from solution import *

# Capacitat + LRU: un get encertat compta com a us (rellotge explicit, sense empats)
c = TTLCache(capacity=2, ttl=5)
c.put("a", 1)                        # t=0
c.tick(1)
c.put("b", 2)                        # t=1
c.tick(1)
assert c.get("a") == 1               # t=2, refresca a
c.tick(1)
c.put("c", 3)                        # t=3 -> expulsa b (stamp 1)
assert c.get("b") is None, "s'hauria d'haver expulsat la menys recent"
assert c.keys() == ["c", "a"], c.keys()

# Un get encertat refresca l'edat (no la deixa envellir)
d = TTLCache(capacity=3, ttl=5)
d.put("x", 9)
d.tick(4)
assert d.get("x") == 9, "a edat 4 encara es valida"
d.tick(1)
assert d.get("x") == 9, "el get anterior n'havia refrescat l'edat"

# Frontera sense refrescar (keys() no refresca): viva a edat < ttl, morta a edat == ttl
g = TTLCache(capacity=3, ttl=5)
g.put("y", 1)
g.tick(4)
assert g.keys() == ["y"], g.keys()
g.tick(1)
assert g.keys() == [], "a edat == ttl ja ha de caducar"
assert g.get("y") is None

# get encertat refresca la recencia (i keys() ho reflecteix)
e = TTLCache(capacity=2, ttl=100)
e.put("a", 1)                        # t=0
e.tick(1)
e.put("b", 2)                        # t=1
e.tick(1)
e.get("a")                           # t=2
e.tick(1)
e.put("c", 3)                        # t=3 -> expulsa b
assert e.keys() == ["c", "a"], e.keys()
assert e.get("b") is None

# put sobre una clau viva actualitza valor i recencia
f = TTLCache(capacity=2, ttl=100)
f.put("k", 1)                        # t=0
f.tick(1)
f.put("j", 2)                        # t=1
f.tick(1)
f.put("k", 5)                        # t=2
f.tick(1)
f.put("z", 3)                        # t=3 -> expulsa j
assert f.get("j") is None            # expulsada en inserir z
assert f.keys() == ["z", "k"], f.keys()   # z (t=3) abans de k (t=2, refrescada)
assert f.get("k") == 5
print('OK')"""
