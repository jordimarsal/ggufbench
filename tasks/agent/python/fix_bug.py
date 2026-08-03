ID = "fix_bug"
LANG = "python"
GOAL = "Fix the bug in solution.py so that add(2,3) returns 5"
INITIAL_FILES = {"solution.py": "def add(a,b):\n    return a-b", "test_solution.py": "from solution import *\nassert add(2,3)==5\nassert add(1,1)==2\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
