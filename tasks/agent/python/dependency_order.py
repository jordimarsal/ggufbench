ID = "dependency_order"
LANG = "python"
GOAL = "Arregla els imports entre solution.py i utils.py perquè el programa funcioni correctament."
INITIAL_FILES = {
    "solution.py": "from utils import format_name\n\ndef greet(name):\n    return 'Hello, ' + format_name(name)\n\nprint(greet('alice'))",
    "utils.py": "def capitalize(s):\n    return s.upper()\n\ndef format_name(name):\n    return capitalize(name)",
    "test_solution.py": "import subprocess\nresult = subprocess.run(['python', 'solution.py'], capture_output=True, text=True)\nassert result.returncode == 0, f'Error: {result.stderr}'\nassert 'Alice' in result.stdout, f'Sortida incorrecta: {result.stdout}'\nprint('OK')"
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
