ID = "num_report_expert"
LANG = "bash"
PROMPT = """Implementa tres funcions (carregables amb `source solution.sh`) per analitzar
fitxers numerics. El fitxer te un enter no negatiu per linia; les linies buides i
les que comencen per `#` (amb espais opcions davant) es salten.

- num_stats FILE -> imprimeix `count min max mean` separat per espais; mean amb
  EXACTAMENT 2 decimals amb PUNT decimal, mai coma (p.ex. 13.00). Sense numeros:
  imprimeix `0`.
- num_hist FILE WIDTH -> bucket = valor // WIDTH; imprimeix UNA linia per bucket
  NO buit, en ordre ascendent, format `lo-hi:count` (lo = i*WIDTH,
  hi = (i+1)*WIDTH-1). Sense numeros: no imprimeix res.
- num_quantile FILE P -> P enter 0..100: index = floor(P*(n-1)) sobre els valors
  ordenats creixentment; imprimeix aquell valor. Sense numeros: imprimeix `NA`."""
TEST_CODE = """source solution.sh
f=$(mktemp); g=$(mktemp); h=$(mktemp)
printf '10\\n20\\n30\\n# x\\n\\n40\\n' > "$f"
[ "$(num_stats "$f")" = "4 10 40 25.00" ] || { echo "stats1: $(num_stats "$f")"; exit 1; }
[ "$(num_hist "$f" 10)" = "$(printf '10-19:1\\n20-29:1\\n30-39:1\\n40-49:1')" ] || { echo "hist1: $(num_hist "$f" 10)"; exit 1; }
[ "$(num_quantile "$f" 0)" = "10" ] || { echo "q0"; exit 1; }
[ "$(num_quantile "$f" 50)" = "20" ] || { echo "q50"; exit 1; }
[ "$(num_quantile "$f" 100)" = "40" ] || { echo "q100"; exit 1; }
printf '1\\n25\\n' > "$g"
[ "$(num_stats "$g")" = "2 1 25 13.00" ] || { echo "stats2: $(num_stats "$g")"; exit 1; }
[ "$(num_hist "$g" 10)" = "$(printf '0-9:1\\n20-29:1')" ] || { echo "hist2 (buit al mig): $(num_hist "$g" 10)"; exit 1; }
printf '# nomes comentaris\\n\\n   \\n' > "$h"
[ "$(num_stats "$h")" = "0" ] || { echo "stats3"; exit 1; }
[ "$(num_quantile "$h" 50)" = "NA" ] || { echo "q3"; exit 1; }
[ -z "$(num_hist "$h" 10)" ] || { echo "hist3"; exit 1; }
rm -f "$f" "$g" "$h"
echo OK"""
