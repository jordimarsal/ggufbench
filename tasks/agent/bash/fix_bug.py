ID = "fix_bug"
LANG = "bash"
GOAL = "Fix the bug in solution.sh so that add returns the sum instead of difference"
INITIAL_FILES = {"solution.sh": "add() { echo $(($1-$2)); }", "test_solution.sh": "source solution.sh\n[ \"$(add 2 3)\" = \"5\" ] || exit 1\necho OK"}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
