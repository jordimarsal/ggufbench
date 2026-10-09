ID = "min_stack_hard"
LANG = "java"
PROMPT = """Implementa una classe Solution amb constructor buit i metodes d'instancia push(int
x), pop(), top() i getMin(). getMin ha de treballar sense recorrer la pila (pila auxiliar)
i sobre una pila buida retorna -1; pop sobre pila buida no ha de fer res."""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        Solution s = new Solution();
        s.push(5); s.push(2); s.push(7);
        if (s.getMin() != 2) throw new RuntimeException("fail");
        if (s.top() != 7) throw new RuntimeException("fail");
        s.pop();
        if (s.getMin() != 2 || s.top() != 2) throw new RuntimeException("fail");
        s.pop();
        if (s.getMin() != 5 || s.top() != 5) throw new RuntimeException("fail");
        s.pop(); s.pop();
        if (s.getMin() != -1) throw new RuntimeException("fail");
        Solution d = new Solution();
        d.push(3); d.push(3); d.push(1);
        d.pop();
        if (d.getMin() != 3) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
