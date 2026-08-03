ID = "refactor"
LANG = "java"
GOAL = "Refactor Solution.java to use more efficient algorithm for fibonacci"
INITIAL_FILES = {"Solution.java": "public class Solution {\n    public static int fibonacci(int n) {\n        if (n <= 1) return n;\n        return fibonacci(n-1) + fibonacci(n-2);\n    }\n}", "Test.java": "public class Test {\n    public static void main(String[] args) {\n        if (Solution.fibonacci(10) != 55) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"}
TEST_FILE = "Test.java"
MAX_TURNS = 8
