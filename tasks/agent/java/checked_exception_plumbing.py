ID = "checked_exception_plumbing"
LANG = "java"
GOAL = "Arregla Solution.java perquè passi els tests. El mètode readFile llança IOException però processFiles no ho gestiona."
INITIAL_FILES = {
    "Solution.java": "import java.io.*;\n\npublic class Solution {\n    public static String readFile(String path) throws IOException {\n        BufferedReader r = new BufferedReader(new FileReader(path));\n        StringBuilder sb = new StringBuilder();\n        String line;\n        while ((line = r.readLine()) != null) sb.append(line);\n        return sb.toString();\n    }\n\n    public static void processFiles() {\n        System.out.println(readFile(\"data.txt\"));\n    }\n}",
    "Test.java": "import java.io.*;\nimport java.nio.file.*;\n\npublic class Test {\n    public static void main(String[] args) throws Exception {\n        Files.writeString(Path.of(\"data.txt\"), \"hello world\");\n        try { Solution.processFiles(); } catch (IOException e) { throw new RuntimeException(\"fail\", e); }\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 8
