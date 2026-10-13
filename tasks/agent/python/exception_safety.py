ID = "exception_safety"
LANG = "python"
GOAL = "Afegeix gestió d'excepcions a solution.py: divide(a,b) ha de llançar ValueError si b==0; get_item(lst,idx) ha de llançar IndexError si idx fora de rang; parse_number(s) ha de llançar ValueError si no és un nombre."
INITIAL_FILES = {
    "solution.py": "def divide(a, b):\n    return a / b\n\ndef get_item(lst, idx):\n    return lst[idx]\n\ndef parse_number(s):\n    return int(s)",
    "test_solution.py": "from solution import *\ntry:\n    divide(1, 0)\n    assert False, 'No va llençar ValueError'\nexcept ValueError:\n    pass\ntry:\n    get_item([1,2], 5)\n    assert False, 'No va llençar IndexError'\nexcept IndexError:\n    pass\ntry:\n    parse_number('abc')\n    assert False, 'No va llençar ValueError'\nexcept ValueError:\n    pass\nprint('OK')"
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
