ID = "fix_compile_error"
LANG = "java"
GOAL = "Fix the compilation errors across both classes so that Main compiles and runs successfully."
INITIAL_FILES = {"Solution.java": "public class Solution {\n    public static int add(double a, double b) {\n        return (int)(a + b);\n    }\n}", "Test.java": "public class Test {\n    public static void main(String[] args) {\n        if (Solution.add(2, 3) != 5) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"}
TEST_FILE = "Test.java"
MAX_TURNS = 8
