ID = "debug"
LANG = "bash"
GOAL = "Debug solution.sh - the reverse function is not working correctly"
INITIAL_FILES = {"solution.sh": "reverse() { echo $1; }", "test_solution.sh": "source solution.sh\n[ \"$(reverse abc)\" = \"cba\" ] || exit 1\necho OK"}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
