ID = "simple_math"
LANG = "bash"
PROMPT = "Implementa una funció add que suma dos números"
TEST_CODE = "source solution.sh\n[ \"$(add 2 3)\" = \"5\" ] || exit 1\n[ \"$(add -1 1)\" = \"0\" ] || exit 1\necho OK"