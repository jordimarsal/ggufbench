ID = "space_traps"
LANG = "bash"
GOAL = 'Crea un script que compti el nombre de fitxers .txt dins del directori "my project". El nom del directori conté espais.'
INITIAL_FILES = {
    "solution.sh": "#!/bin/bash\n# Compta els fitxers .txt a my project/\ncount=$(find 'my project' -name '*.txt' | wc -l)\necho $count",
    "test_solution.sh": "mkdir -p 'my project'\necho 'hello' > 'my project/a.txt'\necho 'world' > 'my project/b.txt'\nbash solution.sh | grep -q '^2$' || exit 1\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
