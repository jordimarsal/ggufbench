ID = "refactor"
LANG = "bash"
GOAL = "Refactor solution.sh to use a more efficient approach for counting words"
INITIAL_FILES = {"solution.sh": "count_words() { local count=0; for word in $1; do count=$((count+1)); done; echo $count; }", "test_solution.sh": "source solution.sh\n[ \"$(count_words 'hello world')\" = \"2\" ] || exit 1\necho OK"}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
