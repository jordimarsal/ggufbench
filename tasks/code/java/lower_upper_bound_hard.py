ID = "lower_upper_bound_hard"
LANG = "java"
PROMPT = """Implementa una classe Solution amb dos metodes estatics de busqueda binaria sobre un
array ORDENAT amb duplicats: lowerBound(int[] a, int t) retorna el primer index amb
a[i] >= t (a.length si no n'hi ha) i upperBound(int[] a, int t) el primer index amb
a[i] > t (a.length si no n'hi ha)."""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        int[] a = {1, 2, 2, 2, 5, 7};
        if (Solution.lowerBound(a, 2) != 1) throw new RuntimeException("fail");
        if (Solution.upperBound(a, 2) != 4) throw new RuntimeException("fail");
        if (Solution.lowerBound(a, 3) != 4) throw new RuntimeException("fail");
        if (Solution.upperBound(a, 3) != 4) throw new RuntimeException("fail");
        if (Solution.lowerBound(a, 0) != 0) throw new RuntimeException("fail");
        if (Solution.upperBound(a, 8) != 6) throw new RuntimeException("fail");
        int[] b = {5, 5, 5};
        if (Solution.lowerBound(b, 5) != 0 || Solution.upperBound(b, 5) != 3)
            throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
