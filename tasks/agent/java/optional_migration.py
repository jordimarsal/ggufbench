ID = "optional_migration"
LANG = "java"
GOAL = "Migra Solution.java de retornar null a Optional<T>. Test.java crida els mètodes i espera que no llancin NPE."
INITIAL_FILES = {
    "Solution.java": "import java.util.*;\n\npublic class Solution {\n    private final List<String> items;\n\n    public Solution(List<String> items) {\n        this.items = items;\n    }\n\n    public String findFirst() {\n        return items.isEmpty() ? null : items.get(0);\n    }\n\n    public String findByIndex(int idx) {\n        if (idx < 0 || idx >= items.size()) return null;\n        return items.get(idx);\n    }\n}",
    "Test.java": "import java.util.*;\n\npublic class Test {\n    public static void main(String[] args) {\n        Solution s1 = new Solution(Arrays.asList(\"a\", \"b\"));\n        if (!s1.findFirst().orElse(\"\").equals(\"a\")) throw new RuntimeException(\"fail: first\");\n        if (!s1.findByIndex(1).orElse(\"\").equals(\"b\")) throw new RuntimeException(\"fail: by index\");\n        // Empty list — absent values come back as Optional.empty(), never null\n        Solution s2 = new Solution(Collections.emptyList());\n        if (s2.findFirst().isPresent()) throw new RuntimeException(\"fail: empty first should be absent\");\n        if (s2.findByIndex(0).isPresent()) throw new RuntimeException(\"fail: empty index should be absent\");\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 8
