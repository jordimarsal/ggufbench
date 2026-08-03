ID = "sum_list"
LANG = "bash"
PROMPT = "Implementa una funció sum_list que suma els arguments passats"
TEST_CODE = "source solution.sh\n[ \"$(sum_list 1 2 3)\" = \"6\" ] || exit 1\n[ \"$(sum_list -1 0 1)\" = \"0\" ] || exit 1\necho OK"