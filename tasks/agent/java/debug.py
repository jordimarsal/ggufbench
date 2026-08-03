ID = "debug"
LANG = "java"
GOAL = "Debug Solution.java - reverseString method is not working correctly"
INITIAL_FILES = {"Solution.java": "public class Solution {\n    public static String reverseString(String s) {\n        return s;\n    }\n}", "Test.java": "public class Test {\n    public static void main(String[] args) {\n        if (!Solution.reverseString(\"abc\").equals(\"cba\")) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"}
TEST_FILE = "Test.java"
MAX_TURNS = 8
