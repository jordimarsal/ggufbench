ID = "count_words"
LANG = "bash"
PROMPT = "Implementa una funció count_words que retorna el nombre de paraules"
TEST_CODE = "source solution.sh\n[ \"$(count_words 'hello world')\" = \"2\" ] || exit 1\n[ \"$(count_words 'a b c d')\" = \"4\" ] || exit 1\n[ \"$(count_words '')\" = \"0\" ] || exit 1\necho OK"
