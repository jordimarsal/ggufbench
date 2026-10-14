ID = "schedule_slots_expert"
LANG = "java"
PROMPT = """Implementa Solution.schedule(int[][] meetings): assigna reunions [inici, final) a sales
i retorna el pla.

Regles:
- Cada reunio es {inici, final} amb 0 <= inici < final.
- Una sala es pot reutilitzar quan la reunio nova comenca a o despres del final de l'ultima
  de la sala (intervals semi-oberts: final == inici es valid).
- Processa les reunions per inici ascendent (empat: final ascendent) i posa cada reunio a
  la primera sala lliure (index mes baix); si cap es lliure, obre una sala nova.
- Retorna un String: una linia per sala `R<k>: [a,b) [c,d)` amb les reunions en ordre
  d'assignacio (sales de 1 en endavant, sense salts) i una ultima linia `rooms: <n>`.
  Sense reunions: nomes `rooms: 0`.
- Una reunio invalida (inici < 0 o final <= inici) ha de llançar IllegalArgumentException."""
TEST_CODE = """public class Test {
    static void eq(String got, String expected, String label) {
        if (!got.equals(expected)) {
            throw new RuntimeException(label + "\\n--- got:\\n" + got + "\\n--- expected:\\n" + expected);
        }
    }

    public static void main(String[] args) {
        eq(Solution.schedule(new int[][]{}), "rooms: 0", "buit");
        eq(Solution.schedule(new int[][]{{0, 30}, {30, 60}}),
           "R1: [0,30) [30,60)\\nrooms: 1", "reutilitzacio exacta");
        eq(Solution.schedule(new int[][]{{0, 30}, {10, 20}}),
           "R1: [0,30)\\nR2: [10,20)\\nrooms: 2", "niuades");
        eq(Solution.schedule(new int[][]{{5, 10}, {0, 3}}),
           "R1: [0,3) [5,10)\\nrooms: 1", "ordre d'entrada irrelevante");
        eq(Solution.schedule(new int[][]{{0, 5}, {5, 10}, {10, 15}}),
           "R1: [0,5) [5,10) [10,15)\\nrooms: 1", "cadena");
        eq(Solution.schedule(new int[][]{{0, 10}, {5, 15}, {11, 12}}),
           "R1: [0,10) [11,12)\\nR2: [5,15)\\nrooms: 2", "greedy per sala mes baixa");
        for (int[][] bad : new int[][][]{{{5, 5}}, {{-1, 3}}, {{10, 2}}}) {
            try {
                Solution.schedule(bad);
                throw new RuntimeException("hauria de fallar");
            } catch (IllegalArgumentException expected) {
                // correcte
            }
        }
        System.out.println("OK");
    }
}"""
