ID = "subst_hard"
LANG = "bash"
PROMPT = """Implementa una funcio subst template que substitueixi cada marc {{NOM}} pel valor de la
variable d'entorn NOM i escrigui el resultat a stdout. Un marc la variable del qual no esta
definida es substitueix per cadena buida. La resta del text queda intacta."""
TEST_CODE = 'source solution.sh\nout=$(VAR=hola subst \'a {{VAR}} b\')\n[ "$out" = "a hola b" ] || exit 1\nout=$(A=1 B=2 subst \'{{A}}-{{B}}-{{C}}\')\n[ "$out" = "1-2-" ] || exit 1\nout=$(subst \'sense marcs\')\n[ "$out" = "sense marcs" ] || exit 1\nout=$(NOM="amb espais" subst \'x={{NOM}}\')\n[ "$out" = "x=amb espais" ] || exit 1\necho OK'
