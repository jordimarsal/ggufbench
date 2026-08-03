ID = "count_words"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic countWords(String s) que retorna el nombre de paraules"
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (Solution.countWords("hello world") != 2) throw new RuntimeException("fail");
        if (Solution.countWords("a b c d") != 4) throw new RuntimeException("fail");
        if (Solution.countWords("") != 0) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
