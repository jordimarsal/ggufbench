ID = "bubble_sort"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic bubbleSort(int[] arr) que retorna l'array ordenat"
TEST_CODE = """import java.util.Arrays;
public class Test {
    public static void main(String[] args) {
        int[] r1 = Solution.bubbleSort(new int[]{3,1,2});
        if (!Arrays.equals(r1, new int[]{1,2,3})) throw new RuntimeException("fail");
        int[] r2 = Solution.bubbleSort(new int[]{});
        if (r2.length != 0) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
