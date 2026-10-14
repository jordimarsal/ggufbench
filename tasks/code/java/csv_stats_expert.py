ID = "csv_stats_expert"
LANG = "java"
PROMPT = """Implementa Solution.report(String path) que retorni un informe de vendes com a String.

El fitxer te una linia per venda: `region,producte,quantitat,preu_unitari`
- quantitat: enter positiu; preu_unitari: decimal amb EXACTAMENT 2 decimals.
- Linies buides o nomes espais: es salten. Linies que comencen per # (despres d'espais
  opcionals): comentaris, es salten.
- Qualsevol altra linia es INVALIDA: es compta i es descarta (no afecta res mes).

Informe, exactament (separat per \\n i sense salt final):
  region,total_units,revenue
  <region>,<unitats>,<ingressos>
  ...
  invalid: <n>
- Una linia per regio, ordenades alfabeticament; unitats = suma de quantitats;
  ingressos = suma de quantitat*preu amb 2 decimals i punt decimal.
- Si no hi ha cap linia valida, nomes la capcalera i la linia `invalid`."""
EXTRA_FILES = {
    "sales.csv": (
        "# setmana 12\n"
        "north,widget,3,10.00\n"
        "south,cable,2,4.50\n"
        "\n"
        "north,widget,2,10.00\n"
        "south,cable,1,4.00\n"
        "east,gizmo,0,9.99\n"
        "west,thing,x,2.00\n"
        "north,thing,1,1.5\n"
        "south,cable,1,4.50,extra\n"
    ),
}
TEST_CODE = """import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Test {
    static void eq(String got, String expected, String label) {
        if (!got.equals(expected)) {
            throw new RuntimeException(label + "\\n--- got:\\n" + got + "\\n--- expected:\\n" + expected);
        }
    }

    public static void main(String[] args) throws IOException {
        eq(Solution.report("sales.csv"),
           "region,total_units,revenue\\nnorth,5,50.00\\nsouth,3,13.00\\ninvalid: 4",
           "sales.csv");

        Files.writeString(Path.of("only_comments.csv"), "# res\\n\\n");
        eq(Solution.report("only_comments.csv"),
           "region,total_units,revenue\\ninvalid: 0", "nomes comentaris");

        Files.writeString(Path.of("bad.csv"), "north,a,1,2.5\\nnorth,b,-1,2.00\\nnorth,c,1,2.00\\n");
        eq(Solution.report("bad.csv"),
           "region,total_units,revenue\\nnorth,1,2.00\\ninvalid: 2", "invalides");

        Files.writeString(Path.of("sort.csv"), "zz,last,2,0.05\\naa,first,1,0.10\\n");
        eq(Solution.report("sort.csv"),
           "region,total_units,revenue\\naa,1,0.10\\nzz,2,0.10\\ninvalid: 0", "ordenacio");
        System.out.println("OK");
    }
}"""
