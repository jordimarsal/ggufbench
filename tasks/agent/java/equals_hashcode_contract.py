ID = "equals_hashcode_contract"
LANG = "java"
GOAL = "Arregla Solution.java perquè passi els tests. equals/hashCode estan mal implementats i el HashMap no troba les entrades."
INITIAL_FILES = {
    "Solution.java": "import java.util.*;\n\npublic class Solution {\n    private final String name;\n    private final int age;\n\n    public Solution(String name, int age) {\n        this.name = name;\n        this.age = age;\n    }\n\n    @Override\n    public boolean equals(Object o) {\n        if (!(o instanceof Solution)) return false;\n        Solution s = (Solution) o;\n        return name.equals(s.name);\n    }\n\n    @Override\n    public int hashCode() {\n        return name.hashCode();\n    }\n}",
    "Test.java": "import java.util.*;\n\npublic class Test {\n    public static void main(String[] args) {\n        Map<Solution, String> map = new HashMap<>();\n        map.put(new Solution(\"Alice\", 30), \"A\");\n        map.put(new Solution(\"Bob\", 25), \"B\");\n        if (!map.containsKey(new Solution(\"Alice\", 31))) throw new RuntimeException(\"fail: lookup broken\");\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 8
