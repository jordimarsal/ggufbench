ID = "simple_math"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic add(int a, int b) que retorna a+b"
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (Solution.add(2,3) != 5) throw new RuntimeException("fail");
        if (Solution.add(-1,1) != 0) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""