ID = "bubble_sort"
LANG = "bash"
PROMPT = "Implementa una funció bubble_sort que ordena els arguments numèrics"
TEST_CODE = "source solution.sh\n[ \"$(bubble_sort 3 1 2)\" = \"1 2 3\" ] || exit 1\n[ \"$(bubble_sort 5 4 3 2 1)\" = \"1 2 3 4 5\" ] || exit 1\necho OK"
