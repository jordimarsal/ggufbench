ID = "config_migration"
LANG = "python"
GOAL = "Migrar la configuració de solution.py: canvia el nom de la funció get_user a fetch_user i el paràmetre user_id a uid. Actualitza també les referències a test_solution.py."
INITIAL_FILES = {
    "solution.py": "def get_user(user_id):\n    return {'id': user_id, 'name': 'Alice'}\n\nprint(get_user(42))",
    "test_solution.py": "from solution import *\nresult = fetch_user(42)\nassert result['id'] == 42\nassert result['name'] == 'Alice'\nprint('OK')"
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
