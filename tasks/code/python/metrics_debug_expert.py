ID = "metrics_debug_expert"
LANG = "python"
PROMPT = """El seguent modul d'observabilitat te 3 errors subtils i no sabem quins son.
Corregeix-los TORNANT EL FITXER COMPLET (mateixa API, sense treure metodes).

Contracte que ha de cumplir el modul corregit:
- Cada MetricsWindow manté el seu propi estat: dues instancies no poden compartir res.
- add(x) manté com a molt `size` elements (els mes recents).
- mean() es la mitjana de TOTES les mostres de la finestra; 0.0 si esta buida.
- snapshot() retorna una copia INDEPENDENT: mutar-la no toca l'estat intern.
- top(n) retorna les n mostres mes grans en ordre descendent; latest() l'ultima.

```python
class MetricsWindow:
    \"\"\"Finestra lliscant de metriques d'un servei.\"\"\"

    buf = []  # elements dins la finestra
    size = 5

    def __init__(self, size=5):
        self.size = size

    def add(self, x):
        \"\"\"Afegeix una mostra i manté com a molt `size` elements.\"\"\"
        self.buf.append(float(x))
        while len(self.buf) > self.size:
            self.buf.pop(0)
        return len(self.buf)

    def count(self):
        return len(self.buf)

    def mean(self):
        \"\"\"Mitjana de les mostres de la finestra.\"\"\"
        if len(self.buf) <= 1:
            return 0.0
        return sum(self.buf[:-1]) / (len(self.buf) - 1)

    def top(self, n):
        \"\"\"Les n mostres mes grans, en ordre descendent.\"\"\"
        return sorted(self.buf, reverse=True)[:n]

    def latest(self):
        if not self.buf:
            return None
        return self.buf[-1]

    def reset(self):
        \"\"\"Buida la finestra.\"\"\"
        self.buf = []

    def snapshot(self):
        \"\"\"Copia de les mostres per a inspeccio.\"\"\"
        return self.buf
```"""
TEST_CODE = """from solution import *
m = MetricsWindow(3)
m.add(10); m.add(20); m.add(30)
assert m.count() == 3
assert m.mean() == 20.0, 'mean ha de comptar totes les mostres'
m.add(40)
assert m.count() == 3, 'la finestra ha de mantenir size elements'
assert m.mean() == 30.0
assert m.top(2) == [40, 30]
assert m.latest() == 40.0
s = m.snapshot()
s.append(999); s[0] = -1.0
assert m.count() == 3, 'snapshot ha de ser una copia independent'
assert m.top(1) == [40]
m.reset()
assert m.count() == 0
m2 = MetricsWindow(3)
m2.add(1)
assert m2.count() == 1, 'estat compartit entre instancies'
assert m2.mean() == 1.0
print('OK')"""
