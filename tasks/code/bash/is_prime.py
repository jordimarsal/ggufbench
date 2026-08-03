ID = "is_prime"
LANG = "bash"
PROMPT = "Implementa una funció is_prime que retorna 'true' si és primer, 'false' altrament"
TEST_CODE = "source solution.sh\n[ \"$(is_prime 2)\" = \"true\" ] || exit 1\n[ \"$(is_prime 3)\" = \"true\" ] || exit 1\n[ \"$(is_prime 4)\" = \"false\" ] || exit 1\n[ \"$(is_prime 17)\" = \"true\" ] || exit 1\n[ \"$(is_prime 1)\" = \"false\" ] || exit 1\necho OK"
