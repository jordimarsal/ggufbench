ID = "shape_area_contract"
LANG = "java"
GOAL = "Arregla Solution.java perquè la classe Circle calcula l'àrea amb el diàmetre en lloc del radi: àrea ha de ser PI*(r²), no PI*(d²)."
INITIAL_FILES = {
    "Solution.java": "import java.util.*;\n\npublic class Solution {\n    public static double computeTotalArea(List<Shape> shapes) {\n        double sum = 0;\n        for (Shape s : shapes) sum += s.area();\n        return sum;\n    }\n}",
    "Circle.java": "class Circle implements Shape {\n    final int diameter; // stored as diameter, not radius\n    Circle(int d) { diameter=d; }\n    @Override\n    public double area() {\n        // BUG: using diameter directly instead of converting to radius\n        return Math.PI * diameter * diameter;\n    }\n}",
    "Rectangle.java": "class Rectangle implements Shape {\n    final int width, height;\n    Rectangle(int w, int h) { width=w; height=h; }\n    @Override\n    public double area() { return width * height; }\n}",
    "Triangle.java": "class Triangle implements Shape {\n    final int base, height;\n    Triangle(int b, int h) { base=b; height=h; }\n    @Override\n    public double area() { return 0.5 * base * height; }\n}",
    "Shape.java": "interface Shape {\n    double area();\n}",
    "Test.java": "import java.util.*;\n\npublic class Test {\n    public static void main(String[] args) {\n        List<Shape> shapes = Arrays.asList(\n            new Circle(10),       // r=5 => area should be PI*25 ≈ 78.54\n            new Rectangle(6, 4),   // area = 24\n            new Triangle(8, 3)     // area = 12\n        );\n        double total = Solution.computeTotalArea(shapes);\n        if (Math.abs(total - (Math.PI*25 + 24 + 12)) > 0.01)\n            throw new RuntimeException(\"fail: wrong total=\" + total);\n        System.out.println(\"OK\");\n    }\n}"
}
TEST_FILE = "Test.java"
MAX_TURNS = 14
