ID = "debug"
LANG = "python"
GOAL = "Debug solution.py - the reverse_string function is not working correctly"
INITIAL_FILES = {"solution.py": "def reverse_string(s):\n    return s", "test_solution.py": "from solution import *\nassert reverse_string('abc')=='cba'\nassert reverse_string('')==''\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
