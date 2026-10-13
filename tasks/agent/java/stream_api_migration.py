ID = "stream_api_migration"
LANG = "java"
GOAL = "Migra Solution.java de loops imperatius a Stream API. El resultat ha de ser idèntic — Test.java verifica els mateixos valors."
INITIAL_FILES = {
    "Solution.java": "import java.util.*;\nimport java.util.stream.*;\n\npublic class Solution {\n    public static List<String> filterAndTransform(List<String> words, int minLen) {\n        List<String> result = new ArrayList<>();\n        for (String w : words) {\n            if (w.length() >= minLen) {\n                result.add(w.toUpperCase());\n            }\n        }\n        return result;\n    }\n\n    public static Map<String, Integer> countByLength(List<String> words) {\n        Map<String, Integer> map = new HashMap<>();\n        for (String w : words) {\n            String key = String.valueOf(w.length());\n            map.put(key, map.getOrDefault(key, 0) + 1);\n        }\n        return map;\n    }\n}",
    "Test.java": "import java.util.*;\n\npublic class Test {\n    public static void main(String[] args) {\n        List<String> words = Arrays.asList(\"hi\", \"hello\", \"world\", \"java\", \"stream\", \"api\");\n        List<String> filtered = Solution.filterAndTransform(words, 4);\n        if (!filtered.equals(Arrays.asList(\"HELLO\", \"WORLD\", \"JAVA\", \"STREAM\", \"API\")))\n            throw new RuntimeException(\"fail: filterAndTransform\");\n        Map<String, Integer> counts = Solution.countByLength(words);\n        if (counts.get(\"2\") != 1 || counts.get(\"5\") != 3 || counts.get(\"4\") != 2)\n            throw new RuntimeException(\"fail: countByLength\");\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 8
