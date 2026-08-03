ID = "remove_duplicates"
LANG = "bash"
PROMPT = "Implementa una funció remove_duplicates que elimina duplicats dels arguments"
TEST_CODE = "source solution.sh\n[ \"$(remove_duplicates 1 2 2 3)\" = \"1 2 3\" ] || exit 1\n[ \"$(remove_duplicates a b a)\" = \"a b\" ] || exit 1\necho OK"
