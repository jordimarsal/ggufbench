ID = "refactor"
LANG = "python"
GOAL = "Refactor solution.py to use a more efficient algorithm for fibonacci"
INITIAL_FILES = {"solution.py": "def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)", "test_solution.py": "from solution import *\nassert fibonacci(10)==55\nassert fibonacci(20)==6765\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
