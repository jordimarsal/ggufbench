ID = "sum_list"
LANG = "java"
PROMPT = "Implementa una classe Solution amb mètode estàtic sumList(int[] arr) que retorna la suma dels elements"
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (Solution.sumList(new int[]{1,2,3}) != 6) throw new RuntimeException("fail");
        if (Solution.sumList(new int[]{-1,0,1}) != 0) throw new RuntimeException("fail");
        if (Solution.sumList(new int[]{}) != 0) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""