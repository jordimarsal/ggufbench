ID = "reverse_string"
LANG = "bash"
PROMPT = "Implementa una funció reverse_string que retorna la string invertida"
TEST_CODE = "source solution.sh\n[ \"$(reverse_string abc)\" = \"cba\" ] || exit 1\n[ \"$(reverse_string)\" = \"\" ] || exit 1\necho OK"