ID = "refactor_guard"
LANG = "python"
GOAL = "Refactor solution.py: rename calculate_total to compute_total and change its parameter name from items_list to products. Update all references including those in test_solution.py."
INITIAL_FILES = {"solution.py": "def calculate_total(items_list):\n    total = 0\n    for item in items_list:\n        total += item['price'] * item['quantity']\n    return total", "test_solution.py": "from solution import *\nassert calculate_total([{'price': 10, 'quantity': 2}]) == 20\nprint('OK')"}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
