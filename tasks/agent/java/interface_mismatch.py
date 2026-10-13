ID = "interface_mismatch"
LANG = "java"
GOAL = "Arregla Solution.java perquè passi els tests. La classe implementa add() però Test.java crida multiply()."
INITIAL_FILES = {"Solution.java": "public class Solution {\n    public static int add(int a, int b) {\n        return a + b;\n    }\n}", "Test.java": "public class Test {\n    public static void main(String[] args) {\n        if (Solution.multiply(3, 4) != 12) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"}
TEST_FILE = "Test.java"
MAX_TURNS = 8
