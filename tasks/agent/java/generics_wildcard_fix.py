ID = "generics_wildcard_fix"
LANG = "java"
GOAL = "Arregla Solution.java perquè passi els tests. El mètode sumNumbers no compila amb List<Double>."
INITIAL_FILES = {
    "Solution.java": "import java.util.*;\n\npublic class Solution {\n    public static double sumNumbers(List<Integer> nums) {\n        double total = 0;\n        for (int n : nums) total += n;\n        return total;\n    }\n}",
    "Test.java": "import java.util.*;\n\npublic class Test {\n    public static void main(String[] args) {\n        List<Double> d = Arrays.asList(1.5, 2.5);\n        if (Math.abs(Solution.sumNumbers(d) - 4.0) > 0.001) throw new RuntimeException(\"fail\");\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 8
