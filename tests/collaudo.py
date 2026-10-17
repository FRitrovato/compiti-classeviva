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
sys.argv = ["compiti_classeviva.py", "--classe", "2A", "--no-open", "--uscita", str(uscita)]

oggi = date.today()
g1 = m.prossimo_giorno_scuola(oggi, False)
g2 = m.prossimo_giorno_scuola(g1, False)

# Il finto ClasseViva: risponde sempre le stesse cose.
m.ClasseViva.accedi = lambda self: setattr(self, "id", "1")
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

html = pagine[0].read_text(encoding="utf-8")
testo = testi[0].read_text(encoding="utf-8")
for atteso in ("Classe 2A", "Geometria: aree pag. 99", "Portare il goniometro",
               "città e perché", "Orario settimanale", "diario scritto a mano"):
    assert atteso in html, f"nella pagina manca: {atteso}"
assert "CONTENERE ERRORI" in html, "manca l'avviso sull'orario nella pagina"
for atteso in ("*Matematica*", "*Inglese*", "diario scritto a mano", "CONTENERE ERRORI"):
    assert atteso in testo, f"nel testo WhatsApp manca: {atteso}"
assert pdf[0].read_bytes()[:4] == b"%PDF"
assert "G1234567X" not in html + testo and "password-finta" not in html + testo, "credenziali nei fogli!"

print("COLLAUDO OK: pagina, PDF e testo WhatsApp prodotti correttamente, nessuna credenziale nei fogli.")
