ID = "lru_cache_hard"
LANG = "python"
PROMPT = """Implementa una classe LRUCache(capacity) amb get(key) (retorna el valor o -1 si no hi
es) i put(key, value), amb eviccio del menys recentment usat quan s'arriba a la capacitat.
get i put han de ser O(1) amortitzat (per exemple dict + llista doblement enllacada)."""
TEST_CODE = """from solution import *
c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) == -1
c.put(4, 4)
assert c.get(1) == -1
assert c.get(3) == 3
assert c.get(4) == 4
c2 = LRUCache(1)
c2.put(1, 'a')
c2.put(1, 'b')
assert c2.get(1) == 'b'
assert c2.get(9) == -1
print('OK')"""
