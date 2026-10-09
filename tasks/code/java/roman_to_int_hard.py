ID = "roman_to_int_hard"
LANG = "java"
PROMPT = """Implementa una classe Solution amb metode estatic romanToInt(String s) que converteixi
un nombre roma (I, V, X, L, C, D, M) al seu valor enter, incloent els casos subtractius
(IV, IX, XL, XC, CD, CM)."""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (Solution.romanToInt("III") != 3) throw new RuntimeException("fail");
        if (Solution.romanToInt("IV") != 4) throw new RuntimeException("fail");
        if (Solution.romanToInt("IX") != 9) throw new RuntimeException("fail");
        if (Solution.romanToInt("LVIII") != 58) throw new RuntimeException("fail");
        if (Solution.romanToInt("MCMXCIV") != 1994) throw new RuntimeException("fail");
        if (Solution.romanToInt("CDXLIV") != 444) throw new RuntimeException("fail");
        System.out.println("OK");
    }
}"""
