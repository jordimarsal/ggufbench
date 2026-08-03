ID = "fibonacci"
LANG = "bash"
PROMPT = "Implementa una funció fibonacci que retorna l'n-èssim número de Fibonacci"
TEST_CODE = "source solution.sh\n[ \"$(fibonacci 0)\" = \"0\" ] || exit 1\n[ \"$(fibonacci 1)\" = \"1\" ] || exit 1\n[ \"$(fibonacci 10)\" = \"55\" ] || exit 1\necho OK"
