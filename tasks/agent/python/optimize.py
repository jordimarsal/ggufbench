ID = "optimize"
LANG = "python"
GOAL = "Optimize the sum_list function in solution.py to use built-in functions"
INITIAL_FILES = {"solution.py": "def sum_list(lst):\n    total = 0\n    for x in lst:\n        total += x\n    return total", "test_solution.py": "from solution import *\nassert sum_list([1,2,3])==6\nassert sum_list([])==0\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
