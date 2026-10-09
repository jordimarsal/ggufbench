ID = "two_sum_count_hard"
LANG = "python"
PROMPT = """Implementa count_pairs_with_sum(nums, target): quantes parelles d'índexs (i, j)
amb i < j compleixen nums[i] + nums[j] == target. Amb la llista gran del test (20.000
elements) ha de respondre a l'instant: la força bruta O(n^2) no passa el test."""
TEST_CODE = """from solution import *
import time
assert count_pairs_with_sum([1, 2, 3, 4, 5], 6) == 2
assert count_pairs_with_sum([3, 3, 3], 6) == 3
assert count_pairs_with_sum([], 5) == 0
assert count_pairs_with_sum([0, 0], 0) == 1
assert count_pairs_with_sum([-1, 1, -1, 1], 0) == 4
data = list(range(20000))
t0 = time.time()
n = count_pairs_with_sum(data, 19999)
t1 = time.time()
assert n == 10000, n
assert t1 - t0 < 5.0, "massa lent: cal O(n) amb taula de frequencies"
print('OK')"""
