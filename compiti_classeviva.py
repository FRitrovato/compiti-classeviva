#!/usr/bin/env python3
"""
compiti_classeviva.py

L'app ClasseViva non ha l'orario, e i compiti NON si possono stampare.
Questo programma li prende dal registro e prepara un foglio pulito,
da leggere sul telefono o stampare in A4.

Cosa fa:
  1. chiede le credenziali ClasseViva del genitore (NON le salva da nessuna parte);
  2. scarica i compiti in arrivo (Agenda + Didattica) e li raggruppa per giorno;
  3. aggiunge l'orario: da orario.csv se c'e', altrimenti ricostruito dal registro;
  4. prepara tre file: una pagina HTML (con bottone Stampa), un PDF, un testo per WhatsApp.

ATTENZIONE: usa l'API REST NON ufficiale, la stessa delle app Spaggiari
(documentata da progetti open source come open-viva/endpoints e Classeviva.py).
Non e' un prodotto Spaggiari, ne' della scuola. Puo' smettere di funzionare
in qualunque momento, se Spaggiari cambia qualcosa.

Uso:
    python compiti_classeviva.py                 # tutti i compiti in arrivo + orario
    python compiti_classeviva.py --domani        # solo il prossimo giorno di scuola
    python compiti_classeviva.py --data 2026-10-16
    python compiti_classeviva.py --dal 2026-10-19 --al 2026-10-23
    python compiti_classeviva.py --senza-classe  # senza il nome della classe in testa al foglio

Licenza GPL-3.0. Ciao / Francesco Ritrovato

PS: le credenziali restano tra te e Spaggiari. Il programma non scrive niente
    su disco tranne i fogli che produce, e non manda niente a nessun altro.
"""

import argparse
import getpass
import html
import json
import re
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# requests e' l'unica dipendenza obbligatoria. Se manca, inutile proseguire.
try:
    import requests
except ImportError:
    sys.exit("Manca 'requests'. Installalo con:  pip install requests")


# Ci presentiamo a Spaggiari come la sua app Android.
# Senza questi header il server ci chiude la porta in faccia.
BASE = "https://web.spaggiari.eu"
HEADERS = {
    "Z-Dev-ApiKey": "Tg1NWEwNGIgIC0K",
    "User-Agent": "CVVS/std/4.2.3 Android/12",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE,
    "Referer": f"{BASE}/home/app/default/login.php?target=&mode=",
}
# weekday() di Python parte da lunedi' = 0. Questa lista va in quell'ordine.
GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
# La cartella dello script. Qui cerchiamo orario.csv (facoltativo).
QUI = Path(__file__).resolve().parent



def sigla_classe(descrizione):
    """Dal registro "2A QUALCOSA" prende solo la sigla "2A". Se non la riconosce, niente."""
    # ATTENZIONE: "classe_ident" sembra la sigla ma NON lo e': e' un codice numerico interno.
    # La sigla vera e' la prima parola di "classe_desc". Verificato su un account reale.
    prima = str(descrizione or "").strip().split(" ")[0]
    return prima.upper() if re.fullmatch(r"[1-5][A-Za-z]{1,3}", prima) else ""


# ================================================================ ACCESSO
# Tutto quello che parla con Spaggiari sta qui dentro.
# Il resto del programma non sa nemmeno che esiste un server.
class ClasseViva:
    def __init__(self, utente, password, studente_id=None, debug=False, target="genitori"):
        # target: "genitori" o "studenti". Per noi e' quasi sempre genitori.
        self.target = target
        # Una sola sessione HTTP per tutto: i cookie del login restano attaccati qui.
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.utente, self.password = utente, password
        # L'id NUMERICO dello studente. Se non lo diamo noi, lo scopre il login.
        self.id = studente_id
        # rest/w1 (nuovo) oppure rest/v1 (classico): lo decide il login che va a buon fine.
        self.rest = None
        self.debug = debug
        # La classe dello studente (es. "3B"): la dice il registro stesso, al login.
        self.classe = ""

    def _dump(self, nome, dati):
        # Solo con --debug: salva la risposta grezza, cosi' vediamo cosa dice davvero il server.
        # OCCHIO: debug_whoami.json contiene i dati anagrafici. Non farlo girare in giro.
        if self.debug:
            (QUI / f"debug_{nome}.json").write_text(
                json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8")

    def accedi(self):
        """Prima prova il login 'web' (rest/w1), poi quello classico (rest/v1)."""
        # Due strade. Spaggiari ogni tanto ne cambia una: con due, almeno una di solito regge.
        try:
            self._accedi_web()
            return
        except Exception as e:
            print(f"[i] login web non riuscito ({e}), provo il login classico...")
        self._accedi_v1()

    def _accedi_web(self):
        # Passo 1: apriamo la pagina di login, solo per farci dare il cookie di sessione.
        self.s.get(f"{BASE}/home/app/default/login.php?target=&mode=", timeout=15)
        # Passo 2: mandiamo utente e password, come farebbe il browser.
        r = self.s.post(f"{BASE}/auth-p7/app/default/AuthApi4.php?a=aLoginPwd",
                        data={"cid": "", "uid": self.utente, "pwd": self.password,
                              "pin": "", "target": self.target}, timeout=15)
        # 422 = credenziali sbagliate. Inutile insistere.
        if r.status_code == 422:
            raise RuntimeError("credenziali rifiutate")
        r.raise_for_status()
        self.rest = f"{BASE}/rest/w1"
        # Passo 3: "chi sono?". Ci restituisce l'id dello studente da usare dappertutto.
        chi = self.s.get(f"{self.rest}/misc/whoami", timeout=15)
        chi.raise_for_status()
        info = chi.json()
        self._dump("whoami", info)
        if not self.id:
            self.id = str(info["id"])
        self.classe = sigla_classe(info.get("classe_desc"))

    def _accedi_v1(self):
        # Il login storico: un JSON con utente e password, in cambio un TOKEN.
        r = self.s.post(f"{BASE}/rest/v1/auth/login",
                        json={"ident": None, "uid": self.utente, "pass": self.password},
                        timeout=15)
        dati = r.json()
        # Nel dump il token NON ci va: e' una chiave di casa, non si lascia sul tavolo.
        self._dump("login_v1", {k: v for k, v in dati.items() if k != "token"})
        if "token" not in dati:
            raise SystemExit(f"Login fallito: {dati.get('error') or dati}")
        # Da qui in poi ogni richiesta porta il token nell'header.
        self.s.headers["Z-Auth-Token"] = dati["token"]
        self.rest = f"{BASE}/rest/v1"
        if not self.id:
            # ident e' tipo "S1234567X": ci servono solo le cifre.
            self.id = "".join(c for c in dati["ident"] if c.isdigit())

    def get(self, percorso, nome):
        # Il mattone di tutte le letture: GET su /students/{id}/qualcosa, risposta in JSON.
        r = self.s.get(f"{self.rest}/students/{self.id}/{percorso}", timeout=20)
        r.raise_for_status()
        dati = r.json()
        self._dump(nome, dati)
        return dati

    def agenda(self, dal, al=None):
        # L'Agenda: compiti (AGHW) e annotazioni (AGNT) messi dai docenti in un intervallo di date.
        # Le date vanno nel formato AAAAMMGG, tutto attaccato.
        a, b = dal.strftime("%Y%m%d"), (al or dal).strftime("%Y%m%d")
        try:
            return self.get(f"agendav2/all/{a}/{b}", "agenda")["agenda"]
        except requests.HTTPError:
            # agendav2 non c'e'? Proviamo la versione vecchia.
            return self.get(f"agenda/all/{a}/{b}", "agenda")["agenda"]

    def compiti_didattica(self):
        # I compiti caricati in "Didattica". Spesso il testo VERO sta qui,
        # mentre in Agenda c'e' solo un rimando tipo "compiti inseriti in Didattica".
        try:
            return self.get("homeworks/index", "compiti").get("items", [])
        except requests.HTTPError:
            # Se la scuola non usa questa sezione, nessun dramma: andiamo avanti senza.
            return []

    def lezioni(self, dal, al):
        # Le lezioni firmate dai docenti: giorno, ora, materia. Ci servono per ricostruire l'orario.
        return self.get(f"lessons/{dal:%Y%m%d}/{al:%Y%m%d}", "lezioni")["lessons"]



# ================================================================ LOGICA
# Qui non si parla con nessuno. Si prendono dati e si mettono in ordine.

def prossimo_giorno_scuola(oggi, sabato):
    # Domani. A meno che domani sia domenica (o sabato, se il sabato non si va).
    # Quindi il venerdi' sera ti da' il lunedi'. Ed e' giusto cosi'.
    g = oggi + timedelta(days=1)
    while g.weekday() == 6 or (g.weekday() == 5 and not sabato):
        g += timedelta(days=1)
    return g


def orario_da_csv(percorso):
    """orario.csv: giorno;ora;materia  (giorno 1=lun ... 6=sab)."""
    # La fonte BUONA: l'orario ufficiale scritto a mano.
    # Le righe che non hanno 3 pezzi o non iniziano con un numero (i commenti) le saltiamo.
    orario = defaultdict(dict)
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        parti = [p.strip() for p in riga.split(";")]
        if len(parti) == 3 and parti[0].isdigit():
            # Nel file lunedi' = 1, in Python lunedi' = 0. Da qui il -1.
            orario[int(parti[0]) - 1][int(parti[1])] = parti[2]
    return orario


def _data(testo):
    try:
        return datetime.strptime((testo or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _materia_valida(nome):
    nome = (nome or "").strip().title()
    # Sostegno e supplenze NON dicono niente sull'orario della classe. Fuori.
    if not nome or any(x in nome.lower() for x in ("sostegno", "supplenza")):
        return ""
    return nome


def orario_da_lezioni(lezioni, oggi=None):
    """Ricostruisce l'orario dalle lezioni firmate sul registro."""
    # Il PIANO B, quando orario.csv non c'e'.
    # Per ogni casella (giorno, ora) contiamo le materie firmate dai docenti.
    # Le ultime due settimane valgono DOPPIO: l'orario di settembre spesso e' provvisorio.
    # Su una classe reale (ottobre 2026), confrontato con l'orario ufficiale: da 11 a 18 caselle giuste su 30.
    #
    # E i compiti? Le date di consegna dicono in quali GIORNI c'e' una materia, e li abbiamo
    # provati: anche solo come spareggio, su una classe reale peggioravano il risultato. Gli errori veri
    # sono tra materie dello stesso docente negli stessi giorni (es. Matematica e Scienze),
    # e li' sapere il giorno non serve. Misurato, non supposto: per questo NON li usiamo.
    #
    # Avvertenza onesta: resta una ricostruzione. Dove i dati non bastano, lo dice con "(?)".
    oggi = oggi or date.today()
    punti = defaultdict(Counter)
    for l in lezioni:
        d = _data(l.get("evtDate"))
        materia = _materia_valida(l.get("subjectDesc"))
        try:
            durata = int(l.get("evtDuration") or 1)
            ora = int(l["evtHPos"])
        except (KeyError, ValueError, TypeError):
            continue  # lezione con dati monchi: la ignoriamo
        if not d or not materia:
            continue
        peso = 2 if (oggi - d).days <= 14 else 1
        for h in range(ora, ora + durata):  # una lezione di 2 ore occupa 2 caselle
            punti[(d.weekday(), h)][materia] += peso

    orario = defaultdict(dict)
    for (g, h), voti in punti.items():
        top = voti.most_common(2)
        # Ci fidiamo solo se c'e' un vincitore chiaro.
        if len(top) == 1 and top[0][1] >= 1 or top[0][1] >= 2 and top[0][1] >= 1.5 * top[1][1]:
            orario[g][h] = top[0][0]
        else:  # dati discordanti: mostro i due candidati
            # Meglio un punto interrogativo onesto che una materia sbagliata nello zaino.
            orario[g][h] = " / ".join(m for m, _ in top) + " (?)"
    return orario


def giorni_scuola(dal, al, sabato):
    # Tutti i giorni tra dal e al, domeniche escluse (e sabati, se a scuola non si va).
    g, out = dal, []
    while g <= al:
        if g.weekday() < 5 or (g.weekday() == 5 and sabato):
            out.append(g)
        g += timedelta(days=1)
    return out


def _riga(materia, docente, testo, tipo):
    # Una voce del foglio, sempre nella stessa forma. Le maiuscole del registro le addomestichiamo.
    return {"tipo": tipo, "materia": (materia or "").strip().title(),
            "docente": (docente or "").strip().title(), "testo": testo.strip()}


def compiti_per_giorno(eventi, didattica, giorni):
    """Unisce agenda e compiti di Didattica, raggruppati per giorno di consegna."""
    # Il cuore del programma. Due fonti, un'unica lista, ZERO doppioni.
    per_id = {h.get("evtId"): h for h in didattica}
    validi = {str(g) for g in giorni}
    usati, per_giorno = set(), defaultdict(list)

    # Giro 1: l'Agenda.
    for e in eventi:
        g = (e.get("evtDatetimeBegin") or "")[:10]
        if g not in validi:
            continue
        testo = (e.get("notes") or "").strip()
        # Se la voce d'agenda punta a un compito in Didattica, prendiamo il testo da li'.
        # E ci segniamo che quel compito l'abbiamo gia' usato.
        hw = per_id.get(e.get("homeworkId"))
        if hw and (hw.get("homeworkDesc") or "").strip():
            testo = hw["homeworkDesc"]
            usati.add(hw.get("evtId"))
        if testo.strip():
            tipo = "Compito" if e.get("evtCode") == "AGHW" else "Annotazione"
            per_giorno[g].append(_riga(e.get("subjectDesc"), e.get("authorName"), testo, tipo))

    # Giro 2: i compiti di Didattica che l'Agenda non nominava. Data che conta: la SCADENZA.
    for h in didattica:
        g = h.get("expiryDate")
        if g in validi and h.get("evtId") not in usati and (h.get("homeworkDesc") or "").strip():
            per_giorno[g].append(_riga(h.get("subjectDesc"), h.get("teacherName"),
                                       h["homeworkDesc"], "Compito"))

    # In ordine di materia. Le voci senza materia (gli avvisi) in fondo.
    for righe in per_giorno.values():
        righe.sort(key=lambda r: (r["materia"] or "zzz", r["tipo"]))
    return per_giorno



# ================================================================ OUTPUT
# Tre uscite per gli stessi dati: HTML (schermo), PDF (carta), testo (WhatsApp).

# Grafica sobria, pensata per la stampa. Ogni giorno resta intero sulla stessa pagina.
CSS = """
body{font-family:Georgia,serif;max-width:780px;margin:24px auto;color:#111;padding:0 16px}
h1{font-size:22px;margin:0}.sub{color:#555;margin:2px 0 8px}
h2{font-size:19px;margin:26px 0 4px;border-bottom:3px solid #111;padding-bottom:3px}
h3{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#444;margin:12px 0 4px}
table{width:100%;border-collapse:collapse;font-size:14px}
td{border-bottom:1px solid #ccc;padding:5px 4px;vertical-align:top}
td.n{width:28px;color:#666}td.m{width:30%;font-weight:bold}td.c{width:24px}
.box{width:15px;height:15px;border:1.5px solid #111;display:inline-block}
.nota{color:#666;font-size:12px;margin-top:6px}
.giorno{break-inside:avoid}
@media print{body{margin:0}.noprint{display:none}}
"""


def titolo(giorni):
    # Un giorno: "Compiti per Giovedi' 15/10/2026". Piu' giorni: "Compiti dal 15/10 al 20/10/2026".
    a, b = giorni[0], giorni[-1]
    if a == b:
        return f"Compiti per {GIORNI[a.weekday()]} {a:%d/%m/%Y}"
    return f"Compiti dal {a:%d/%m} al {b:%d/%m/%Y}"


def genera_pdf(percorso, giorni, orario, origine, per_giorno, studente):
    # Stesso contenuto dell'HTML, ma in PDF A4. Serve reportlab.
    # Se manca, restituiamo False e ci si arrangia con l'HTML. Niente panico.
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table, TableStyle,
                                        Spacer, KeepTogether)
    except ImportError:
        return False
    st = getSampleStyleSheet()
    # Anche Paragraph di reportlab interpreta un mini-HTML: quindi escape anche qui.
    e = html.escape
    stile = TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP")])
    el = [Paragraph(e(titolo(giorni)), st["Title"]), Paragraph(e(studente), st["Normal"])]
    for g in giorni:
        compiti, ore = per_giorno.get(str(g), []), orario.get(g.weekday(), {})
        blocco = [Spacer(1, 8), Paragraph(f"{GIORNI[g.weekday()]} {g:%d/%m}", st["Heading2"])]
        if ore:
            t = Table([[f"{o}ª", ore[o], "[  ]"] for o in sorted(ore)], colWidths=[30, 400, 40])
            t.setStyle(stile)
            blocco += [Paragraph("<b>Orario</b>", st["Normal"]), t, Spacer(1, 4)]
        blocco.append(Paragraph("<b>Compiti e annotazioni</b>", st["Normal"]))
        if compiti:
            dati = [[Paragraph(f"<b>{e(c['materia'] or c['docente'] or '-')}</b>"
                               + (" <i>(nota)</i>" if c["tipo"] != "Compito" else ""), st["Normal"]),
                     Paragraph(e(c["testo"]).replace("\n", "<br/>"), st["Normal"]), "[  ]"]
                    for c in compiti]
            t = Table(dati, colWidths=[140, 290, 40])
            t.setStyle(stile)
            blocco.append(t)
        else:
            blocco.append(Paragraph("Nessun compito registrato.", st["Normal"]))
        # KeepTogether: un giorno NON si spezza mai a cavallo di due pagine.
        el.append(KeepTogether(blocco))
    if origine:
        el.append(Paragraph(f"<font size=8>Orario {e(origine)}.</font>", st["Normal"]))
    el.append(Paragraph("<font size=8><i>Per i compiti fa sempre fede il diario scritto a mano "
                        "dall'alunno.</i></font>", st["Normal"]))
    SimpleDocTemplate(str(percorso), pagesize=A4, leftMargin=40, rightMargin=40,
                      topMargin=40, bottomMargin=40).build(el)
    return True


# L'avvertenza sull'orario ricostruito: stessa frase ovunque (pagina, PDF, WhatsApp).
AVVISO_ORARIO = ("Orario ricostruito in automatico dalle lezioni firmate sul registro: "
                 "PUÒ CONTENERE ERRORI. Fa fede l'orario ufficiale comunicato dalla scuola.")


def testo_whatsapp(giorni, orario, per_giorno, ricostruito=False):
    """Testo pronto da incollare su WhatsApp: niente nomi, solo materie e compiti."""
    # Va nel gruppo dei genitori, quindi PRIVACY prima di tutto:
    # niente scuola, niente classe, niente studente, niente docenti.
    # Gli asterischi sono il grassetto di WhatsApp, i trattini bassi il corsivo.
    righe = [f"📚 *{titolo(giorni).upper()}*"]
    for g in giorni:
        righe.append("")
        righe.append(f"*{GIORNI[g.weekday()].upper()} {g:%d/%m}*")
        ore = orario.get(g.weekday(), {})
        if ore:
            righe.append("🕒 " + " · ".join(f"{o}ª {ore[o]}" for o in sorted(ore)))
        compiti = per_giorno.get(str(g), [])
        if compiti:
            for c in compiti:
                materia = c["materia"] or "Avviso"
                # Tutto su una riga: sul telefono si legge meglio.
                testo = " ".join(c["testo"].split())
                righe.append(f"▪️ *{materia}*: {testo}")
        else:
            righe.append("▪️ Nessun compito registrato")
    # La data di aggiornamento SEMPRE in fondo: chi legge capisce subito se e' roba vecchia.
    if ricostruito and orario:
        righe += ["", f"_\u26a0\ufe0f {AVVISO_ORARIO}_"]
    righe += ["", f"_Aggiornato il {datetime.now():%d/%m alle %H:%M} dal registro elettronico._",
              "_Per i compiti fa sempre fede il diario scritto a mano dall'alunno._"]
    return "\n".join(righe)


# Le sigle per la tabella dell'orario sul web: sul telefono ogni lettera conta.
SIGLE = {
    "italiano": "It", "ita": "It", "storia": "St", "letteratura": "Let",
    "grammatica": "Gr", "antologia": "Ant", "geografia": "Geo",
    "scienze": "Sc", "matematica": "Mat", "geometria": "Geom",
    "tecnologia": "Tec", "approfondimento": "App", "inglese": "Ing",
    "francese": "Fr", "arte": "Ar", "pratica": "P", "teoria": "T",
    "motoria": "Mot", "musica": "Mus", "alternativa": "Alt", "religione": "Rel",
}


# Le materie di piu' parole, cosi' come le scrive il registro, prima di spezzarle.
FRASI = {
    "arte e immagine": "Arte", "educazione fisica": "Mot", "scienze motorie": "Mot",
    "educazione civica": "Civ", "seconda lingua comunitaria": "2L", "lingua inglese": "Ing",
    "lingua francese": "Fr", "lingua spagnola": "Spa", "lingua tedesca": "Ted",
    "strumento musicale": "Strum",
}


def sigla(materia):
    # "Ita/Grammatica" -> "It/Gr", "Arte (pratica)" -> "Ar P". Le parole sconosciute restano come sono.
    basso = materia.lower()
    for frase, corta in FRASI.items():
        basso = basso.replace(frase, corta)
    materia = basso
    pezzi = materia.replace("(", " ").replace(")", " ").replace("/", " / ").split()
    corto = " ".join(SIGLE.get(w.lower(), w[:1].upper() + w[1:]) for w in pezzi)
    return corto.replace(" / ", "/")


def html_pagina_web(classe, orario, giorni, per_giorno, ricostruito=False):
    """Il corpo della pagina: compiti in arrivo + orario della settimana."""
    # Pensata per essere condivisa (gruppo classe, stampa), quindi PRIVACY prima di tutto:
    # al massimo il nome della classe. Niente scuola, niente studenti, niente docenti.
    e = html.escape
    # Il nome della classe sta gia' nel titolo della pagina: qui solo la data, ben visibile.
    out = [f"<p><strong>Aggiornato il {datetime.now():%d/%m/%Y alle %H:%M}</strong></p>"]

    # Prima i compiti: e' quello che il genitore cerca aprendo la pagina dal telefono.
    out.append("<h2>Compiti in arrivo</h2>")
    giorni_pieni = [g for g in giorni if per_giorno.get(str(g))]
    if not giorni_pieni:
        out.append("<p>Nessun compito registrato per i prossimi giorni.</p>")
    for g in giorni_pieni:
        # Il giorno deve SALTARE all'occhio: maiuscolo e grassetto.
        out.append(f"<h3><strong>{GIORNI[g.weekday()].upper()} {g:%d/%m}</strong></h3><ul>")
        for c in per_giorno[str(g)]:
            materia = e(c["materia"] or "Avviso")
            testo = e(" ".join(c["testo"].split()))
            out.append(f"<li><strong>{materia}</strong>: {testo}</li>")
        out.append("</ul>")

    # Poi l'orario della settimana, una tabella sola: righe = ore, colonne = giorni.
    if orario:
        giorni_sett = [d for d in range(6) if orario.get(d)]
        ore = sorted({o for d in giorni_sett for o in orario[d]})
        out.append("<h2>Orario settimanale</h2><table><thead><tr><th></th>")
        out += [f"<th>{GIORNI[d][:3]}</th>" for d in giorni_sett]
        out.append("</tr></thead><tbody>")
        for o in ore:
            out.append(f"<tr><th>{o}ª</th>")
            out += [f"<td>{e(sigla(orario[d].get(o, '')))}</td>" for d in giorni_sett]
            out.append("</tr>")
        out.append("</tbody></table>")
        if ricostruito:
            out.append(f"<p><strong>\u26a0\ufe0f {e(AVVISO_ORARIO)}</strong></p>")

    out.append("<p><em>Dati presi dal registro elettronico. Per i compiti fa sempre fede il diario scritto a mano dall'alunno.</em></p>")
    return "\n".join(out)

def leggi_data(testo):
    # "2026-10-19" -> data vera. Se il formato e' sbagliato, ValueError e ci pensa main().
    return datetime.strptime(testo, "%Y-%m-%d").date()


# Grafica della pagina: leggibile sul telefono, stampabile in A4, chiara o scura secondo il telefono.
STILE_PAGINA = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;max-width:720px;margin:0 auto;padding:16px;color:#1a1a1a;background:#fff;line-height:1.45}
h1{font-size:1.5rem;margin:.2rem 0 .4rem}
h2{font-size:1.15rem;margin:1.6rem 0 .5rem;padding-bottom:.25rem;border-bottom:2px solid #1a1a1a}
h3{font-size:1rem;margin:1.1rem 0 .3rem;color:#333}
ul{padding-left:1.1rem;margin:.2rem 0}li{margin:.25rem 0}
table{width:100%;border-collapse:collapse;font-size:.72rem;table-layout:fixed}
th,td{border:1px solid #ccc;padding:.35rem .25rem;text-align:center;vertical-align:middle;hyphens:auto;-webkit-hyphens:auto;overflow-wrap:break-word}
@media screen and (max-width:520px){table{font-size:.62rem}th,td{padding:.25rem .05rem}tbody th{width:1.4rem}}
thead th{background:#1f3864;color:#fff}tbody th{background:#f1f3f7;width:2.2rem}
tbody tr:nth-child(even) td{background:#fafbfd}
p{margin:.4rem 0}em{color:#666;font-size:.85rem}
.stampa{display:inline-block;margin:.2rem 0 .6rem;padding:.55rem 1rem;font-size:1rem;border:0;border-radius:6px;background:#1f3864;color:#fff;cursor:pointer}
/* STAMPA A4: da telefono o da computer, stessa pagina. Bianco e nero, niente bottone, giorni mai spezzati. */
@page{size:A4 portrait;margin:12mm}
@media print{
 .stampa{display:none}
 body{max-width:none;padding:0;font-size:10.5pt;color:#000;background:#fff}
 h1{font-size:16pt}h2{font-size:12.5pt;border-color:#000;break-after:avoid}h3{font-size:11pt;color:#000;break-after:avoid}
 ul{break-inside:avoid}table{font-size:8pt;break-inside:avoid}
 thead th{background:#ddd !important;color:#000 !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
 tbody th,tbody tr:nth-child(even) td{background:#fff !important}th,td{border-color:#888}
 em{color:#444}
}
@media screen and (prefers-color-scheme:dark){body{background:#121212;color:#eee}th,td{border-color:#444}tbody th{background:#222}tbody tr:nth-child(even) td{background:#1a1a1a}h2{border-color:#eee}h3{color:#ccc}em{color:#aaa}}
"""


def pagina_completa(classe, orario, giorni, per_giorno, ricostruito=False):
    """La pagina HTML finale: titolo, bottone Stampa, compiti in arrivo, orario della settimana."""
    titolo_pagina = f"Classe {classe}" if classe else "Compiti e orario"
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(titolo_pagina)}</title><style>{STILE_PAGINA}</style></head><body>"
            f"<h1>{html.escape(titolo_pagina)}</h1>"
            f"<button class='stampa' onclick='window.print()'>Stampa / salva PDF</button>"
            + html_pagina_web(classe, orario, giorni, per_giorno, ricostruito) + "</body></html>")


# ================================================================ MAIN
# Il regista: chiede, scarica, mette in ordine, salva.

def main():
    # 1. Le opzioni. Senza niente: tutti i compiti in arrivo.
    ap = argparse.ArgumentParser(description="Compiti e orario da ClasseViva, pronti da leggere e stampare")
    ap.add_argument("--domani", action="store_true", help="solo il prossimo giorno di scuola")
    ap.add_argument("--data", help="un solo giorno, AAAA-MM-GG")
    ap.add_argument("--dal", help="inizio periodo, AAAA-MM-GG")
    ap.add_argument("--al", help="fine periodo, AAAA-MM-GG (default: uguale a --dal)")
    ap.add_argument("--classe", default="",
                    help="nome della classe in testa al foglio (di solito non serve: lo legge dal registro)")
    ap.add_argument("--senza-classe", action="store_true",
                    help="non scrivere il nome della classe in testa al foglio")
    ap.add_argument("--sabato", action="store_true", help="la scuola fa lezione anche il sabato")
    ap.add_argument("--uscita", default=".", help="cartella dove salvare i file (default: quella corrente)")
    ap.add_argument("--no-open", action="store_true", help="non aprire il foglio nel browser alla fine")
    ap.add_argument("--debug", action="store_true",
                    help="salva le risposte grezze del server (contengono dati personali: NON condividerle)")
    a = ap.parse_args()

    # 2. Quali giorni. Le date si controllano PRIMA del login.
    oggi = date.today()
    try:
        if a.dal:
            dal = leggi_data(a.dal)
            al = leggi_data(a.al) if a.al else dal
            tutti = False
        elif a.data:
            dal = al = leggi_data(a.data)
            tutti = False
        elif a.domani:
            dal = al = prossimo_giorno_scuola(oggi, a.sabato)
            tutti = False
        else:
            # Da domani in poi, per 60 giorni, mai oltre il 30 giugno (fine anno scolastico).
            dal = prossimo_giorno_scuola(oggi, a.sabato)
            al = min(dal + timedelta(days=60), date(dal.year if dal.month < 9 else dal.year + 1, 6, 30))
            tutti = True
    except ValueError:
        sys.exit("Data non valida: usa il formato AAAA-MM-GG, es. 2026-10-19")
    if al < dal:
        sys.exit("--al deve essere uguale o successiva a --dal")
    giorni = giorni_scuola(dal, al, a.sabato)
    if not giorni:
        sys.exit("Nel periodo indicato non ci sono giorni di scuola.")

    # 3. Le credenziali. Chieste a voce, MAI salvate. La password non compare mentre la scrivi.
    print("Accesso a ClasseViva (le credenziali NON vengono salvate)")
    utente = input("  Codice utente o email del genitore: ").strip()
    password = getpass.getpass("  Password (non si vede mentre scrivi): ")
    cv = ClasseViva(utente, password, None, a.debug, "genitori")
    try:
        cv.accedi()
    except SystemExit:
        raise
    except Exception as err:
        sys.exit(f"[!] Accesso non riuscito: {err}")
    finally:
        password = None  # non la teniamo in giro piu' del necessario
    print("[ok] accesso eseguito")
    # La classe: quella scritta a mano con --classe, altrimenti quella del registro.
    # Con --senza-classe non compare proprio.
    classe = "" if a.senza_classe else (a.classe.strip() or cv.classe)

    # 4. I compiti: Agenda + Didattica, raggruppati per giorno di consegna.
    didattica = cv.compiti_didattica()
    per_giorno = compiti_per_giorno(cv.agenda(giorni[0], giorni[-1]), didattica, giorni)
    if tutti:
        giorni = [g for g in giorni if per_giorno.get(str(g))] or giorni[:1]

    # 5. L'orario. orario.csv accanto al programma vince sempre; altrimenti lo ricostruiamo.
    csv = QUI / "orario.csv"
    if csv.exists():
        orario, origine = orario_da_csv(csv), "da orario.csv"
    else:
        try:
            orario = orario_da_lezioni(cv.lezioni(oggi - timedelta(weeks=4), oggi), oggi)
            origine = "RICOSTRUITO in automatico: può contenere errori, fa fede l'orario ufficiale della scuola"
        except requests.HTTPError:
            orario, origine = {}, ""

    # 6. I file.
    uscita = Path(a.uscita).expanduser()
    uscita.mkdir(parents=True, exist_ok=True)
    nome = (f"compiti_{giorni[0]:%Y-%m-%d}" if len(giorni) == 1
            else f"compiti_{giorni[0]:%Y-%m-%d}_{giorni[-1]:%Y-%m-%d}")
    base = uscita / nome
    pagina = base.with_suffix(".html")
    ricostruito = not csv.exists()
    pagina.write_text(pagina_completa(classe, orario, giorni, per_giorno, ricostruito), encoding="utf-8")
    print(f"[ok] pagina  -> {pagina}")
    if genera_pdf(base.with_suffix(".pdf"), giorni, orario, origine, per_giorno,
                  f"Classe {classe}" if classe else ""):
        print(f"[ok] PDF     -> {base.with_suffix('.pdf')}")
    else:
        print("[i] per avere anche il PDF:  pip install reportlab  (intanto stampa la pagina)")
    base.with_suffix(".txt").write_text(testo_whatsapp(giorni, orario, per_giorno, ricostruito), encoding="utf-8")
    print(f"[ok] testo per WhatsApp -> {base.with_suffix('.txt')}")
    if origine and not csv.exists():
        print("[i] l'orario e' ricostruito dal registro: se non torna, compila orario.csv (vedi il manuale)")
    if a.debug:
        print("[!] ATTENZIONE: i file debug_*.json contengono dati personali. Cancellali, non condividerli.")

    # 7. Apriamo la pagina, cosi' si vede subito il risultato.
    if not a.no_open:
        webbrowser.open(pagina.resolve().as_uri())


if __name__ == "__main__":
    main()
