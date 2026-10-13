ID = "dataclasses_migration"
LANG = "python"
GOAL = "Migra solution.py de l'estructura basada en dicts a dataclasses mantenint el comportament idèntic. Crea una classe User amb camps name (str) i age (int), i modifica process_user perquè accepti instàncies de User en lloc de dicts. Els tests verifiquen que les sortides són idèntiques."
INITIAL_FILES = {
    "solution.py": "# Solution buida - cal implementar-ho tot",
    "test_solution.py": "from solution import *\n\n# Test dataclass creation\nu = User('Alice', 30)\nassert u.name == 'Alice'\nassert u.age == 30\n\n# Test process_user with dataclass\nresult = process_user(u)\nassert result['name'] == 'ALICE'\nassert result['age'] == 60\n\n# Test another instance\nu2 = User('Bob', 25)\nresult2 = process_user(u2)\nassert result2['name'] == 'BOB'\nassert result2['age'] == 50\n\nprint('OK')"
}
TEST_FILE = "test_solution.py"
MAX_TURNS = 8
