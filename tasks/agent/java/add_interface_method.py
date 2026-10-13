ID = "add_interface_method"
LANG = "java"
GOAL = 'Arregla Solution.java perquè passi els tests. Implementa el mètode count() de la interfície DataProcessor.'
INITIAL_FILES = {
    "Solution.java": "import java.util.*;\ninterface DataProcessor {\n    String process(String input);\n    int count();\n}\nclass Solution implements DataProcessor {\n    private List<String> data = Arrays.asList(\"a\", \"b\", \"c\");\n    public String process(String input) {\n        return input.toUpperCase();\n    }\n}",
    "Test.java": "public class Test {\n    public static void main(String[] args) {\n        DataProcessor p = new Solution();\n        if (!p.process(\"hello\").equals(\"HELLO\")) throw new RuntimeException(\"fail\");\n        if (p.count() != 3) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 8
