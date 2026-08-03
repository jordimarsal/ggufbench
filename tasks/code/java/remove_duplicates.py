ID = "remove_duplicates"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic removeDuplicates(int[] arr) que retorna una nova array sense duplicats"
TEST_CODE = """import java.util.Arrays;
public class Test {
    public static void main(String[] args) {
        int[] r1 = Solution.removeDuplicates(new int[]{1,2,2,3});
        if (!Arrays.equals(r1, new int[]{1,2,3})) throw new RuntimeException("fail");
        int[] r2 = Solution.removeDuplicates(new int[]{});
        if (r2.length != 0) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
