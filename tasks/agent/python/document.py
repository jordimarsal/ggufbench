ID = "document"
LANG = "python"
GOAL = "Add docstrings to all functions in solution.py following PEP 257"
INITIAL_FILES = {"solution.py": "def add(a,b):\n    return a+b\n\ndef subtract(a,b):\n    return a-b", "test_solution.py": "from solution import *\nassert add(2,3)==5\nassert subtract(5,2)==3\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
