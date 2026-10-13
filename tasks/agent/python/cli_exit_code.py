ID = "cli_exit_code"
LANG = "python"
GOAL = "Crea calc.sh que accepti tres arguments: operació (add/sub/mul/div), primer nombre i segon nombre. Ha d'imprimir el resultat per stdout i sortir amb codi 0 si tot bé, codi 1 si falten arguments, codi 2 si l'operació és desconeguda, codi 3 si es divideix per zero."
INITIAL_FILES = {
    "calc.sh": "#!/bin/bash\n# Calculadora CLI\nif [ $# -lt 3 ]; then\n    exit 1\nfi\nop=$1\na=$2\nb=$3\nresult=$((a + b))\necho $result",
    "test_solution.sh": "bash calc.sh add 2 3 | grep -q '^5$' || exit 1\nbash calc.sh sub 10 4 | grep -q '^6$' || exit 1\nbash calc.sh mul 3 7 | grep -q '^21$' || exit 1\nbash calc.sh div 8 2 | grep -q '^4$' || exit 1\nbash calc.sh > /dev/null 2>&1; [ $? -eq 1 ] || exit 1\nbash calc.sh foo 1 2 > /dev/null 2>&1; [ $? -eq 2 ] || exit 1\nbash calc.sh div 5 0 > /dev/null 2>&1; [ $? -eq 3 ] || exit 1\necho OK"
}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
