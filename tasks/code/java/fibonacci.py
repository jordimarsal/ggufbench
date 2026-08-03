ID = "fibonacci"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic fibonacci(int n) que retorna l'n-èssim número de Fibonacci"
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (Solution.fibonacci(0) != 0) throw new RuntimeException("fail");
        if (Solution.fibonacci(1) != 1) throw new RuntimeException("fail");
        if (Solution.fibonacci(10) != 55) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
