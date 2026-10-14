ID = "feature_flag_end_to_end"
LANG = "java"
GOAL = """L'informe de l'eina surt sempre amb la capcalera, tambe quan es demana el mode silencios:
l'opcio `--quiet` s'ignora i el registre intern diu sempre `mode=normal`.

Punt d'entrada: `Solution.main(String[] args)`.

Contracte:
- Sense arguments: s'escriu la capcalera `== REPORT ==` i les files de dades a stdout, i una
  linia de registre a stderr amb `mode=normal`.
- Amb `--quiet`: la capcalera NO s'ha d'escriure (les files de dades si) i el registre ha de
  dir `mode=quiet`.
- El codi de sortida es 0 en els dos casos.

Esbrina on fallen les coses: el punt d'entrada no és l'únic fitxer del projecte."""
INITIAL_FILES = {
    "Solution.java": '''public class Solution {
    public static void main(String[] args) {
        Options opts = Cli.parse(args);
        Logger.info("mode=" + (opts.quiet ? "quiet" : "normal"));
        Report report = Report.build();
        System.out.print(Renderer.render(report, opts.quiet));
    }
}
''',
    "Cli.java": '''import java.util.ArrayList;
import java.util.List;

class Options {
    boolean quiet = false;
    List<String> inputs = new ArrayList<>();
}

class Cli {
    // BUG: mai mira si hi ha --quiet a la linia de comandes
    static Options parse(String[] args) {
        Options opts = new Options();
        for (String a : args) {
            if (!a.startsWith("--")) {
                opts.inputs.add(a);
            }
        }
        return opts;
    }
}
''',
    "Report.java": '''import java.util.ArrayList;
import java.util.List;

class Report {
    final List<String> rows;

    Report(List<String> rows) {
        this.rows = rows;
    }

    static Report build() {
        List<String> rows = new ArrayList<>();
        rows.add("row-a 10.00");
        rows.add("row-b 25.50");
        return new Report(rows);
    }
}
''',
    "Renderer.java": '''class Renderer {
    // BUG: el parametre quiet s'ignora i la capcalera surt sempre
    static String render(Report report, boolean quiet) {
        StringBuilder sb = new StringBuilder();
        sb.append("== REPORT ==").append('\\n');
        for (String row : report.rows) {
            sb.append(row).append('\\n');
        }
        return sb.toString();
    }
}
''',
    "Logger.java": '''class Logger {
    static void info(String msg) {
        System.err.println(msg);
    }
}
''',
    "Test.java": '''import java.io.ByteArrayOutputStream;
import java.io.PrintStream;

public class Test {
    static String[] run(String... args) throws Exception {
        PrintStream oldOut = System.out;
        PrintStream oldErr = System.err;
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        System.setOut(new PrintStream(out));
        System.setErr(new PrintStream(err));
        try {
            Solution.main(args);
        } finally {
            System.setOut(oldOut);
            System.setErr(oldErr);
        }
        return new String[]{out.toString(), err.toString()};
    }

    public static void main(String[] args) throws Exception {
        String[] plain = run();
        if (!plain[0].contains("== REPORT ==")) throw new RuntimeException("falta la capcalera");
        if (!plain[0].contains("row-a") || !plain[0].contains("row-b"))
            throw new RuntimeException("falten files de dades");
        if (!plain[1].contains("mode=normal")) throw new RuntimeException("registre: " + plain[1]);

        String[] quiet = run("--quiet");
        if (quiet[0].contains("== REPORT ==")) throw new RuntimeException("--quiet ha de suprimir la capcalera");
        if (!quiet[0].contains("row-a") || !quiet[0].contains("row-b"))
            throw new RuntimeException("--quiet no pot perdre les files");
        if (!quiet[1].contains("mode=quiet")) throw new RuntimeException("registre en quiet: " + quiet[1]);
        System.out.println("OK");
    }
}
''',
}
TEST_FILE = "Test.java"
MAX_TURNS = 14
