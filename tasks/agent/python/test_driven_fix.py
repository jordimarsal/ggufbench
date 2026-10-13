ID = "test_driven_fix"
LANG = "python"
GOAL = "Arregla solution.py perquè passi els tests de test_solution.py sense modificar mai el fitxer de tests."
INITIAL_FILES = {"solution.py": "def sum_list(numbers):\n    return 0", "test_solution.py": "from solution import *\nassert sum_list([1, 2, 3]) == 6\nassert sum_list([]) == 0\nassert sum_list([-1, 1]) == 0\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
