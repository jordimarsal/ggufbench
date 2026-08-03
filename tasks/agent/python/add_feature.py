ID = "add_feature"
LANG = "python"
GOAL = "Add a multiply function to solution.py that multiplies two numbers"
INITIAL_FILES = {"solution.py": "def add(a,b):\n    return a+b", "test_solution.py": "from solution import *\nassert add(2,3)==5\nassert multiply(2,3)==6\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
