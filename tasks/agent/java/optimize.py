ID = "optimize"
LANG = "java"
GOAL = "Optimize Solution.java to use more efficient approach for isPrime"
INITIAL_FILES = {"Solution.java": "public class Solution {\n    public static boolean isPrime(int n) {\n        for (int i = 2; i < n; i++) {\n            if (n % i == 0) return false;\n        }\n        return n > 1;\n    }\n}", "Test.java": "public class Test {\n    public static void main(String[] args) {\n        if (!Solution.isPrime(17)) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"}
TEST_FILE = "Test.java"
MAX_TURNS = 8
