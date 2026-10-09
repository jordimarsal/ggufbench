ID = "merge_intervals_hard"
LANG = "python"
PROMPT = """Implementa merge_intervals(intervals): donada una llista d'intervals [start, end] sense
ordre garantit, retorna la llista fusionada i ordenada. Dos intervals que es toquen (com
[1,2] i [2,3]) es fusionen. La llista buida retorna []."""
TEST_CODE = """from solution import *
assert merge_intervals([]) == []
assert merge_intervals([[1, 2]]) == [[1, 2]]
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 2], [2, 3], [3, 5]]) == [[1, 5]]
assert merge_intervals([[5, 6], [1, 3], [2, 4]]) == [[1, 4], [5, 6]]
print('OK')"""
