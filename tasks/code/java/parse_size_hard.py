ID = "parse_size_hard"
LANG = "java"
PROMPT = """Implementa Solution.parseSize(String text) que retorni la mida en bytes com a long,
amb aquestes regles:

- Numero decimal estricte, sense signe, amb com a maxim un punt decimal i com a minim un
  digit abans i despres del punt si el punt hi es ("0", "512", "1.5" si; ".5", "1.", "1.2.3",
  "-1", "" no).
- Sufix d'unitat opcional insensible a majuscules, amb una "B" final opcional i equivalent:
  K/KB = 1000, M/MB = 1000^2, G/GB = 1000^3, T/TB = 1000^4.
- Espais al principi i al final permesos, i com a maxim un espai entre el numero i la unitat
  (" 4 Gb " es valid).
- Qualsevol altra entrada ha de llançar IllegalArgumentException.
- Si el decimal no es exacte es trunca cap a baix ("1.0005K" -> 1000)."""
TEST_CODE = """public class Test {
    public static void main(String[] args) {
        if (Solution.parseSize("0") != 0L) throw new RuntimeException("fail 0");
        if (Solution.parseSize("512") != 512L) throw new RuntimeException("fail 512");
        if (Solution.parseSize("1K") != 1000L) throw new RuntimeException("fail 1K");
        if (Solution.parseSize("1k") != 1000L) throw new RuntimeException("fail 1k");
        if (Solution.parseSize("1KB") != 1000L) throw new RuntimeException("fail 1KB");
        if (Solution.parseSize("1.5K") != 1500L) throw new RuntimeException("fail 1.5K");
        if (Solution.parseSize("2.5M") != 2500000L) throw new RuntimeException("fail 2.5M");
        if (Solution.parseSize("3G") != 3000000000L) throw new RuntimeException("fail 3G");
        if (Solution.parseSize("1T") != 1000000000000L) throw new RuntimeException("fail 1T");
        if (Solution.parseSize(" 4 Gb ") != 4000000000L) throw new RuntimeException("fail 4 Gb");
        if (Solution.parseSize("1.0005K") != 1000L) throw new RuntimeException("fail trunc");
        String[] bad = {"", "   ", "K", "KB", "1X", "1.2.3K", "-1", ".5K", "1.K", "1Kb2",
                        "1 K K", "1 2K"};
        for (String b : bad) {
            try {
                Solution.parseSize(b);
                throw new RuntimeException("hauria de fallar: [" + b + "]");
            } catch (IllegalArgumentException expected) {
                // correcte
            }
        }
        System.out.println("OK");
    }
}"""
