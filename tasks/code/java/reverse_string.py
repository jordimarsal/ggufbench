ID = "reverse_string"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic reverseString(String s) que retorna la string invertida"
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (!Solution.reverseString("abc").equals("cba")) throw new RuntimeException("fail");
        if (!Solution.reverseString("").equals("")) throw new RuntimeException("fail");
        if (!Solution.reverseString("a").equals("a")) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""