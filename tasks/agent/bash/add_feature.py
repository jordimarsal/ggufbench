ID = "add_feature"
LANG = "bash"
GOAL = "Add a multiply function to solution.sh"
INITIAL_FILES = {"solution.sh": "add() { echo $(($1+$2)); }", "test_solution.sh": "source solution.sh\n[ \"$(add 2 3)\" = \"5\" ] || exit 1\n[ \"$(multiply 2 3)\" = \"6\" ] || exit 1\necho OK"}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
