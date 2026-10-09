ID = "bracket_validator_hard"
LANG = "java"
PROMPT = """Implementa una classe Solution amb metode estatic isValid(String s) que retorni true si
els parentesis/claudators/claus de s estan ben aparellats i niuats; els altres caracters
s'ignoren. String buida retorna true. Correcte: "a(b)c[d]{e}". Incorrecte: "([)]" i "((("."""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (!Solution.isValid("")) throw new RuntimeException("fail");
        if (!Solution.isValid("a(b)c[d]{e}")) throw new RuntimeException("fail");
        if (!Solution.isValid("{[()()]}x")) throw new RuntimeException("fail");
        if (Solution.isValid("([)]")) throw new RuntimeException("fail");
        if (Solution.isValid("(((")) throw new RuntimeException("fail");
        if (Solution.isValid(")(")) throw new RuntimeException("fail");
        if (!Solution.isValid("sense cap tipus")) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
