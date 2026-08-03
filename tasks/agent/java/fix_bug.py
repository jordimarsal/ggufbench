ID = "fix_bug"
LANG = "java"
GOAL = "Fix the bug in Solution.java - add method should return sum, not difference"
INITIAL_FILES = {"Solution.java": "public class Solution {\n    public static int add(int a, int b) {\n        return a - b;\n    }\n}", "Test.java": "public class Test {\n    public static void main(String[] args) {\n        if (Solution.add(2,3) != 5) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"}
TEST_FILE = "Test.java"
MAX_TURNS = 8
