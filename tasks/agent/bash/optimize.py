ID = "optimize"
LANG = "bash"
GOAL = "Optimize the solution.sh to use more efficient built-in commands"
INITIAL_FILES = {"solution.sh": "sum_list() { local sum=0; for x in $@; do sum=$((sum+x)); done; echo $sum; }", "test_solution.sh": "source solution.sh\n[ \"$(sum_list 1 2 3)\" = \"6\" ] || exit 1\necho OK"}
TEST_FILE = "test_solution.sh"
MAX_TURNS = 8
