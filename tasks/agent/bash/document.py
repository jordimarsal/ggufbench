ID = "document"
LANG = "bash"
GOAL = "Add comments to all functions in solution.sh"
INITIAL_FILES = {"solution.sh": "add() { echo $(($1+$2)); }\nsubtract() { echo $(($1-$2)); }", "test_solution.sh": "source solution.sh\n[ \"$(add 2 3)\" = \"5\" ] || exit 1\n[ \"$(subtract 5 2)\" = \"3\" ] || exit 1\necho OK"}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
