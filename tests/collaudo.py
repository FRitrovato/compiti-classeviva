"""
Collaudo con un ClasseViva FINTO: nessuna credenziale vera, nessuna connessione a Spaggiari.

Simula un genitore che lancia il programma, scrive codice e password, e controlla
che escano la pagina, il PDF e il testo per WhatsApp, con i contenuti giusti.
Gira da solo su GitHub, su Windows e su Mac, a ogni modifica.
"""
import builtins
import getpass
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import compiti_classeviva as m  # noqa: E402

uscita = Path(tempfile.mkdtemp())
sys.argv = ["compiti_classeviva.py", "--no-open", "--uscita", str(uscita)]

oggi = date.today()
g1 = m.prossimo_giorno_scuola(oggi, False)
g2 = m.prossimo_giorno_scuola(g1, False)

# Il finto ClasseViva: risponde sempre le stesse cose.
def finto_accesso(self):
    self.id, self.classe = "1", "3B"   # la classe la "dice" il registro finto
m.ClasseViva.accedi = finto_accesso
m.ClasseViva.agenda = lambda self, a, b=None: [
    {"evtCode": "AGNT", "notes": "Portare il goniometro",
     "evtDatetimeBegin": f"{g1}T00:00:00+02:00", "authorName": "Docente"}]
m.ClasseViva.compiti_didattica = lambda self: [
    {"evtId": 1, "homeworkDesc": "Geometria: aree pag. 99, es. 169 e 170",
     "expiryDate": str(g1), "subjectDesc": "MATEMATICA"},
    {"evtId": 2, "homeworkDesc": "Workbook pag. 32, città e perché",
     "expiryDate": str(g2), "subjectDesc": "INGLESE"}]
lunedi = oggi - timedelta(days=oggi.weekday())
m.ClasseViva.lezioni = lambda self, a, b: [
    {"evtDate": str(lunedi - timedelta(weeks=w) + timedelta(days=d)), "evtHPos": h + 1,
     "evtDuration": 1, "subjectDesc": materia}
    for w in (1, 2, 3)
    for d, ore in enumerate([["ITALIANO", "STORIA", "MATEMATICA"], ["TECNOLOGIA", "INGLESE", "ARTE E IMMAGINE"]])
    for h, materia in enumerate(ore)]

# Il finto genitore: scrive codice e password.
builtins.input = lambda prompt="": "G1234567X"
getpass.getpass = lambda prompt="": "password-finta"

m.main()

pagine = list(uscita.glob("compiti_*.html"))
pdf = list(uscita.glob("compiti_*.pdf"))
testi = list(uscita.glob("compiti_*.txt"))
assert len(pagine) == 1 and len(pdf) == 1 and len(testi) == 1, list(uscita.iterdir())
assert pagine[0].name.startswith("compiti_3B_"), pagine[0].name  # la classe nel nome: piu' figli, niente sovrascritture

html = pagine[0].read_text(encoding="utf-8")
testo = testi[0].read_text(encoding="utf-8")
for atteso in ("Classe 3B", "Geometria: aree pag. 99", "Portare il goniometro",
               "città e perché", "Orario settimanale", "diario scritto a mano"):
    assert atteso in html, f"nella pagina manca: {atteso}"
assert "CONTENERE ERRORI" in html, "manca l'avviso sull'orario nella pagina"
for atteso in ("*Matematica*", "*Inglese*", "diario scritto a mano", "CONTENERE ERRORI"):
    assert atteso in testo, f"nel testo WhatsApp manca: {atteso}"
assert pdf[0].read_bytes()[:4] == b"%PDF"
assert "G1234567X" not in html + testo and "password-finta" not in html + testo, "credenziali nei fogli!"

# La sigla della classe: dal testo del registro, mai dal codice numerico interno.
assert m.sigla_classe("2A MEDIA") == "2A" and m.sigla_classe("3b liceo") == "3B"
assert m.sigla_classe("1234567") == "" and m.sigla_classe(None) == "" and m.sigla_classe("") == ""

print("COLLAUDO OK: pagina, PDF e testo WhatsApp prodotti correttamente, nessuna credenziale nei fogli.")

# Genitore con DUE figli: il registro chiede quale. Il programma deve chiederlo e riprovare con l'ident giusto.
class FintaSessione:
    def __init__(self):
        self.headers, self.inviati = {}, []
    def post(self, url, json=None, **kw):
        self.inviati.append(json["ident"])
        class R:
            pass
        r = R()
        if json["ident"] is None:
            r.json = lambda: {"choices": [{"ident": "G1111111A", "name": "Genitore di ROSSI ANNA"},
                                          {"ident": "X2222222B", "name": "Genitore di ROSSI LUCÌA"}],
                              "message": "you must provide a value for the \"ident\" field"}
        else:
            r.json = lambda: {"token": "tok", "ident": json["ident"]}
        return r
cv = m.ClasseViva("genitore@example.com", "password-finta")
cv.s = FintaSessione()
builtins.input = lambda prompt="": "2"
cv._accedi_v1()
assert cv.s.inviati == [None, "X2222222B"], cv.s.inviati
assert cv.id == "2222222", cv.id
print("COLLAUDO OK: con due figli chiede quale e accede con quello scelto.")

# Senza "chi sono" (login classico) la classe si ricava dalle lezioni firmate.
assert m.classe_da_lezioni([{"classDesc": "1C SCUOLA MEDIA"}, {"classDesc": "1C SCUOLA MEDIA"},
                            {"classDesc": "3F"}, {}]) == "1C"
assert m.classe_da_lezioni([]) == "" and m.classe_da_lezioni([{"classDesc": "999"}]) == ""
print("COLLAUDO OK: classe ricavata dalle lezioni quando il registro non la dice al login.")

# E con TRE figli? L'elenco e' lungo quanto serve: si sceglie il terzo.
tre = [{"ident": f"G{i}", "name": f"Genitore di ROSSI FIGLIO{i}"} for i in (1, 2, 3)]
builtins.input = lambda prompt="": "3"
assert m.scegli_figlio(tre)["ident"] == "G3"
print("COLLAUDO OK: con tre figli si sceglie anche il terzo.")

# Le annotazioni dell'Agenda arrivano SENZA materia: la ricaviamo dal docente che le ha scritte.
lez = [{"authorName": "Prof A", "subjectDesc": "SECONDA LINGUA COMUNITARIA"}] * 5 + \
      [{"authorName": "Prof A", "subjectDesc": "SUPPLENZA"}] * 9 + \
      [{"authorName": "Prof B", "subjectDesc": "ITALIANO"}] * 3 + \
      [{"authorName": "Prof B", "subjectDesc": "EDUCAZIONE CIVICA"}] * 6
doc = m.materie_dei_docenti(lez)
assert doc == {"Prof A": "SECONDA LINGUA COMUNITARIA", "Prof B": "ITALIANO"}, doc
nota = [{"evtCode": "AGNT", "notes": "Studiare pag 14", "authorName": "Prof A",
         "evtDatetimeBegin": f"{g1}T00:00:00+02:00"}]
riga = m.compiti_per_giorno(nota, [], [g1], doc)[str(g1)][0]
assert riga["materia"] == "Seconda Lingua Comunitaria", riga
print("COLLAUDO OK: le annotazioni dell'Agenda prendono la materia del docente.")
