ID = "is_prime"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic isPrime(int n) que retorna true si n és primer, false altrament"
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (!Solution.isPrime(2)) throw new RuntimeException("fail");
        if (!Solution.isPrime(3)) throw new RuntimeException("fail");
        if (Solution.isPrime(4)) throw new RuntimeException("fail");
        if (!Solution.isPrime(17)) throw new RuntimeException("fail");
        if (Solution.isPrime(1)) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
