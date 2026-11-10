#!/usr/bin/env python3
"""
compiti_classeviva.py

Scena tipica, ore 21:30.
  "Hai fatto i compiti?"  "Sì."  "Quali?"  "Boh, non c'erano."  "E oggi in classe?"  "Niente."
Ecco, questo programma esiste per quella scena.

L'app ClasseViva i compiti li ha, ma sparsi tra Agenda e Didattica, e NON si stampano.
Il programma li prende dal registro e prepara un foglio pulito, da leggere sul telefono,
stampare in A4 o incollare nel gruppo WhatsApp. E ci aggiunge quello che l'app non ti dice.

Cosa fa:
  1. chiede codice e password ClasseViva del GENITORE. Di base NON li salva; se vuoi,
     li fa ricordare al portachiavi del computer (MAI in un file);
     se sull'account ci sono piu' figli, chiede di quale;
     la classe (tipo "3B") la legge da solo dal registro: nessuno la deve scrivere;
  2. scarica i compiti in arrivo (Agenda + Didattica), li mette in fila per giorno di
     consegna e li segna: 📌 scritto in Agenda, 🆕 nuovo, ⚠️ verifica;
  3. mette in cima le VERIFICHE dei prossimi 14 giorni, con il conto alla rovescia;
  4. racconta cosa hanno fatto IN CLASSE, ora per ora, con l'argomento scritto dal docente.
     Addio "niente";
  5. l'orario della settimana SOLO se lo chiedi (--orario): ricostruito dal registro
     puo' sbagliare, e lo zaino ormai lo sanno fare;
  6. prepara tre file: una pagina HTML (con bottone Stampa), un PDF, un testo per WhatsApp.

ATTENZIONE: usa l'API REST NON ufficiale, la stessa delle app Spaggiari
(documentata da progetti open source come open-viva/endpoints e Classeviva.py).
Non e' un prodotto Spaggiari, ne' della scuola. Puo' smettere di funzionare
in qualunque momento, se Spaggiari cambia qualcosa.

Uso:
    python compiti_classeviva.py                 # tutti i compiti in arrivo (il caso di tutti i giorni)
    python compiti_classeviva.py --orario        # ...e in fondo anche l'orario della settimana
    python compiti_classeviva.py --domani        # solo il prossimo giorno di scuola
    python compiti_classeviva.py --data 2026-10-16
    python compiti_classeviva.py --dal 2026-10-19 --al 2026-10-23
    python compiti_classeviva.py --cambia-password   # nuova password (e la salva al posto della vecchia)
    python compiti_classeviva.py --dimentica         # cancella codice e password salvati

Licenza GPL-3.0. Gratis, aperto, per sempre. Ciao / Francesco Ritrovato

PS: le credenziali restano tra te, Spaggiari e (se lo chiedi tu) il portachiavi del tuo
    computer. Il programma non le scrive in nessun file e non manda niente a nessun altro.
    Nemmeno a me. Soprattutto a me.
PPS: per i compiti fa fede il diario scritto a mano. Il programma e' solo un alleato.
"""

import argparse
import getpass
import html
import json
import re
import sys
import unicodedata
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


def classe_da_lezioni(lezioni):
    """La sigla che compare piu' spesso nelle lezioni firmate. Se non c'e', niente."""
    # Il piano B per la classe. Ogni lezione firmata dal docente si porta dietro "classDesc"
    # (tipo "2A SCUOLA MEDIA"). Serve quando il login non ci ha detto la classe:
    # succede ai genitori con piu' figli, che entrano dalla porta classica (vedi _accedi_v1).
    # Contiamo e prendiamo la piu' frequente: una supplenza in un'altra classe non ci frega.
    conta = Counter(sigla_classe(l.get("classDesc")) for l in lezioni)
    conta.pop("", None)   # le lezioni senza classe riconoscibile non votano
    return conta.most_common(1)[0][0] if conta else ""


def scegli_figlio(scelte):
    """Piu' figli sullo stesso account: chiede di quale. Con uno solo, nessuna domanda."""
    # Il registro ci manda una lista tipo:
    #   [{"ident": "G1234567X", "name": "Genitore di ROSSI MARIO", ...}, {...}]
    # Il nome lo mostriamo SOLO qui, sullo schermo di chi ha appena scritto la password.
    # Nei fogli (pagina, PDF, WhatsApp) non finisce mai.
    if len(scelte) == 1:
        return scelte[0]
    print("\n  Su questo account ci sono piu' figli. Di chi vuoi i compiti?")
    for n, c in enumerate(scelte, 1):
        # "Genitore di ROSSI MARIO" -> "ROSSI MARIO".
        # Via gli accenti: la finestra nera di Windows li trasforma in geroglifici.
        nome = str(c.get("name", "")).replace("Genitore di ", "")
        nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
        print(f"    {n}. {nome}")
    # Si insiste con gentilezza finche' non arriva un numero sensato.
    while True:
        r = input(f"  Scrivi il numero (1-{len(scelte)}) e premi Invio: ").strip()
        if r.isdigit() and 1 <= int(r) <= len(scelte):
            return scelte[int(r) - 1]
        print("  Numero non valido, riprova.")


# ================================================================ PORTACHIAVI
# Su richiesta, codice e password si possono far ricordare al computer.
# NON in un file: nel portachiavi del sistema, lo stesso dove il browser tiene le sue password.
#   Mac: Portachiavi (Keychain).  Windows: Gestione credenziali.  Linux: Secret Service.
# Cifrate dal sistema e legate al tuo utente. Chi non lo vuole, non risponde "s" e non cambia niente.
SERVIZIO = "compiti-classeviva"


def _portachiavi():
    """Il modulo keyring, se c'e' e se il sistema ha davvero un portachiavi. Altrimenti None."""
    try:
        import keyring
        from keyring.backends import fail
        if isinstance(keyring.get_keyring(), fail.Keyring):
            return None   # es. un Linux senza portachiavi: meglio non fingere
        return keyring
    except Exception:
        return None


def credenziali_salvate():
    """(utente, password) dal portachiavi, oppure (None, None)."""
    k = _portachiavi()
    if not k:
        return None, None
    try:
        utente = k.get_password(SERVIZIO, "utente")
        return (utente, k.get_password(SERVIZIO, utente)) if utente else (None, None)
    except Exception:
        return None, None


def salva_credenziali(utente, password):
    k = _portachiavi()
    if not k:
        print("[i] su questo computer non c'e' un portachiavi utilizzabile: credenziali NON salvate")
        return False
    k.set_password(SERVIZIO, "utente", utente)
    k.set_password(SERVIZIO, utente, password)
    return True


def dimentica_credenziali():
    """Toglie codice e password dal portachiavi. Se non c'erano, nessun dramma."""
    k = _portachiavi()
    utente, _ = credenziali_salvate()
    if not (k and utente):
        return False
    for chiave in (utente, "utente"):
        try:
            k.delete_password(SERVIZIO, chiave)
        except Exception:
            pass
    return True


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
            # Non e' un errore: ai genitori con piu' figli succede SEMPRE (il registro vuole
            # sapere quale figlio, e la porta web non sa chiederlo). Messaggio tranquillo;
            # i dettagli tecnici solo con --debug, per chi li sa leggere.
            print("[i] primo ingresso non riuscito, provo il secondo...")
            if self.debug:
                print(f"    dettaglio: {e}")
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
        # Primo tentativo SENZA dire quale figlio ("ident": None). Con un figlio solo basta cosi'.
        dati = self._login_v1(None)
        # Genitore con PIU' FIGLI: il registro non sa di chi parliamo e invece del token risponde
        #   {"choices": [ ...un elemento per figlio... ],
        #    "message": 'you must provide a value for the "ident" field of payload'}
        # Allora chiediamo al genitore quale figlio e riproviamo con il suo "ident".
        # Visto davvero, il 18 ottobre 2026, sull'account di un papa' con due figli.
        scelte = dati.get("choices") or []
        if "token" not in dati and scelte:
            dati = self._login_v1(scegli_figlio(scelte)["ident"])
        if "token" not in dati:
            # NIENTE risposta grezza a schermo: dentro ci sono nomi e codici. Solo il messaggio.
            raise SystemExit(f"Login fallito: {dati.get('error') or dati.get('message') or 'risposta inattesa (riprova con --debug)'}")
        # Da qui in poi ogni richiesta porta il token nell'header.
        self.s.headers["Z-Auth-Token"] = dati["token"]
        self.rest = f"{BASE}/rest/v1"
        if not self.id:
            # ident e' tipo "S1234567X": ci servono solo le cifre.
            self.id = "".join(c for c in dati["ident"] if c.isdigit())

    def _login_v1(self, ident):
        # Una sola chiamata di login. ident=None: "fai tu". ident="G1234567X": "quel figlio li'".
        r = self.s.post(f"{BASE}/rest/v1/auth/login",
                        json={"ident": ident, "uid": self.utente, "pass": self.password},
                        timeout=15)
        dati = r.json()
        # Nel dump il token NON ci va: e' una chiave di casa, non si lascia sul tavolo.
        self._dump("login_v1", {k: v for k, v in dati.items() if k != "token"})
        return dati

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


def _riga(materia, docente, testo, tipo, assegnato="", fonte="didattica"):
    # Una voce del foglio, sempre nella stessa forma. Le maiuscole del registro le addomestichiamo.
    # "assegnato": il giorno in cui il compito e' stato DATO (AAAA-MM-GG), se il registro lo dice.
    # Serve al bollino NUOVO.
    # "fonte": "agenda" o "didattica". Sul foglio i compiti scritti SOLO in Agenda hanno lo spillo 📌:
    # in Didattica il ragazzo li ritrova, in Agenda e' facile perderli.
    return {"tipo": tipo, "materia": (materia or "").strip().title(),
            "docente": (docente or "").strip().title(), "testo": testo.strip(),
            "assegnato": assegnato or "", "fonte": fonte}


def data_consegna(e):
    """Il giorno in cui una voce d'Agenda va FATTA. Non sempre e' il giorno in cui comincia."""
    # Visto davvero il 10 novembre 2026: "Approfondimento: scrivere riassunto..." andava
    # dal 3 al 10 novembre. Inizio = quando l'hanno dato, fine = quando va consegnato.
    # Prima guardavamo solo l'inizio, e queste voci sparivano dal foglio.
    inizio = (e.get("evtDatetimeBegin") or "")[:10]
    fine = (e.get("evtDatetimeEnd") or "")[:10]
    return fine if fine > inizio and not e.get("isFullDay") else inizio


def materie_dei_docenti(lezioni):
    """Docente -> la materia che insegna di piu' in questa classe (dalle lezioni firmate)."""
    # Serve alle ANNOTAZIONI dell'Agenda: il registro le manda SENZA materia, solo con il
    # nome di chi le ha scritte. Senza questo, sul foglio uscivano come "Avviso".
    # Visto davvero il 20 ottobre 2026: "Studiare pag 14 e 16, i numeri vanno imparati"
    # era della prof di Francese, e il foglio diceva "Avviso".
    # Il nome del docente lo usiamo SOLO qui, come chiave: sui fogli non finisce mai.
    conta = defaultdict(Counter)
    for l in lezioni:
        materia = (l.get("subjectDesc") or "").strip()
        # Supplenze e sostegno non dicono cosa insegna davvero. Educazione civica la fanno
        # in tanti: se vincesse lei, la prof di Italiano diventerebbe "Educazione Civica".
        if not materia or any(x in materia.lower() for x in ("sostegno", "supplenza", "educazione civica")):
            continue
        conta[(l.get("authorName") or "").strip()][materia] += 1
    # Chi insegna due materie (Matematica e Scienze) finisce sotto quella con piu' ore.
    return {doc: c.most_common(1)[0][0] for doc, c in conta.items() if doc}


def compiti_per_giorno(eventi, didattica, giorni, docenti=None):
    """Unisce agenda e compiti di Didattica, raggruppati per giorno di consegna."""
    # Il cuore del programma. Due fonti, un'unica lista, ZERO doppioni.
    per_id = {h.get("evtId"): h for h in didattica}
    validi = {str(g) for g in giorni}
    usati, per_giorno = set(), defaultdict(list)

    # Giro 1: l'Agenda.
    for e in eventi:
        g = data_consegna(e)
        if g not in validi:
            continue
        inizio = (e.get("evtDatetimeBegin") or "")[:10]
        # Se la voce dura piu' giorni, il primo e' quello in cui e' stata data.
        assegnato = inizio if inizio != g else ""
        testo = (e.get("notes") or "").strip()
        # Se la voce d'agenda punta a un compito in Didattica, prendiamo il testo da li'.
        # E ci segniamo che quel compito l'abbiamo gia' usato.
        hw = per_id.get(e.get("homeworkId"))
        fonte = "agenda"   # finche' non scopriamo che rimanda a un compito di Didattica
        if hw and (hw.get("homeworkDesc") or "").strip():
            fonte = "didattica"
            testo = hw["homeworkDesc"]
            assegnato = hw.get("assignmentDate") or assegnato
            usati.add(hw.get("evtId"))
        if testo.strip():
            tipo = "Compito" if e.get("evtCode") == "AGHW" else "Annotazione"
            # La materia: quella del registro; se manca (le annotazioni), quella del docente che l'ha scritta.
            # Se rimanda a Didattica, la materia la sa di sicuro Didattica.
            materia = (e.get("subjectDesc") or (hw or {}).get("subjectDesc")
                       or (docenti or {}).get((e.get("authorName") or "").strip()))
            per_giorno[g].append(_riga(materia, e.get("authorName"), testo, tipo, assegnato, fonte))

    # Giro 2: i compiti di Didattica che l'Agenda non nominava. Data che conta: la SCADENZA.
    for h in didattica:
        g = h.get("expiryDate")
        if g in validi and h.get("evtId") not in usati and (h.get("homeworkDesc") or "").strip():
            per_giorno[g].append(_riga(h.get("subjectDesc"), h.get("teacherName"),
                                       h["homeworkDesc"], "Compito", h.get("assignmentDate")))

    # In ordine di materia. Le voci senza materia (gli avvisi) in fondo.
    for righe in per_giorno.values():
        righe.sort(key=lambda r: (r["materia"] or "zzz", r["tipo"]))
    return per_giorno


# ---------------------------------------------------------------- IL DIARIO DI CLASSE
# Non solo "cosa c'e' da fare", ma anche "cosa hanno fatto". Il registro lo sa:
# ogni lezione firmata ha l'ARGOMENTO, e ogni compito di Didattica la data in cui e' stato DATO.

# Parole che, in un compito o in un avviso, vogliono dire "verifica in arrivo".
VERIFICA = re.compile(r"verific|interrogazion|compito in classe|prova (scritta|orale|pratica)|"
                      r"\btest\b|devoir en classe|contr[oô]le", re.IGNORECASE)

# PRIVACY. I fogli girano nei gruppi dei genitori.
# Certi docenti scrivono "Interrogati: Rossi, Bianchi" o "Assenti: ...". I nomi NON escono:
# tagliamo dal "due punti" fino al punto (o a fine riga).
NOMI_IN_ELENCO = re.compile(r"\b(interrogat[ioe]|assent[ie]|present[ie]|giustificat[ie])\s*:[^.;\n]*",
                            re.IGNORECASE)


def pulisci(testo):
    """Spazi in ordine e nessun elenco di alunni."""
    return " ".join(NOMI_IN_ELENCO.sub(r"\1: (omesso)", testo or "").split())


def giorni_con_lezioni(lezioni, fino_a):
    """I giorni (dal piu' recente) in cui ci sono state lezioni, fino a 'fino_a' compreso."""
    # "Oggi" per la pagina e' l'ultimo giorno DI SCUOLA: di domenica e' il venerdi'.
    # E "il giorno prima" e' quello di scuola prima ancora, non il giorno di calendario.
    return sorted({l.get("evtDate") for l in lezioni if l.get("evtDate") and l["evtDate"] <= str(fino_a)},
                  reverse=True)


def diario_del_giorno(giorno, lezioni, agenda, didattica, docenti):
    """Cosa e' successo in classe un certo giorno: lezioni con argomento, note in Agenda, compiti dati."""
    giorno = str(giorno)
    ore = []
    for l in sorted((l for l in lezioni if l.get("evtDate") == giorno), key=lambda l: int(l.get("evtHPos") or 0)):
        materia = (l.get("subjectDesc") or "").strip()
        if not materia or "sostegno" in materia.lower():
            continue   # il sostegno e' di UN alunno, non della classe: non lo raccontiamo
        tipo = (l.get("lessonType") or "").strip()
        ore.append({"ora": int(l.get("evtHPos") or 0), "materia": materia.title(),
                    # "Lezione" lo diamo per scontato; "Interrogazione", "Prova pratica" invece li diciamo.
                    "tipo": "" if tipo.lower() in ("", "lezione") else tipo,
                    "argomento": pulisci(l.get("lessonArg"))})
    # Certi docenti la lezione la raccontano in Agenda: le note di QUEL giorno, di un giorno solo.
    note = []
    for e in agenda:
        inizio, fine = (e.get("evtDatetimeBegin") or "")[:10], (e.get("evtDatetimeEnd") or "")[:10]
        if inizio == giorno and fine in ("", giorno) and (e.get("notes") or "").strip():
            materia = e.get("subjectDesc") or docenti.get((e.get("authorName") or "").strip()) or ""
            note.append({"materia": materia.title(), "testo": pulisci(e.get("notes"))})
    # I compiti DATI quel giorno (la data di consegna e' un'altra storia).
    dati = [{"materia": (h.get("subjectDesc") or "").title(), "testo": pulisci(h.get("homeworkDesc")),
             "per": h.get("expiryDate") or ""}
            for h in didattica if h.get("assignmentDate") == giorno and (h.get("homeworkDesc") or "").strip()]
    dati.sort(key=lambda d: (d["per"], d["materia"]))
    return {"giorno": datetime.strptime(giorno, "%Y-%m-%d").date(), "ore": ore, "note": note, "dati": dati}


def verifiche_in_arrivo(per_giorno, oggi, entro=14):
    """Verifiche e interrogazioni nei prossimi 'entro' giorni, la piu' vicina per prima."""
    trovate = []
    for g, righe in per_giorno.items():
        d = datetime.strptime(g, "%Y-%m-%d").date()
        if 0 < (d - oggi).days <= entro:
            trovate += [(d, r) for r in righe if VERIFICA.search(r["testo"])]
    return sorted(trovate, key=lambda x: (x[0], x[1]["materia"]))


def tra_quanto(d, oggi):
    """'domani', 'tra 3 giorni'. Il conto alla rovescia che i ragazzi capiscono al volo."""
    n = (d - oggi).days
    return "domani" if n == 1 else f"tra {n} giorni"


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


def testo_whatsapp(giorni, orario, per_giorno, ricostruito=False, diario=None):
    """Testo pronto da incollare su WhatsApp: niente nomi, solo materie e compiti."""
    # Va nel gruppo dei genitori, quindi PRIVACY prima di tutto:
    # niente scuola, niente classe, niente studente, niente docenti.
    # Gli asterischi sono il grassetto di WhatsApp, i trattini bassi il corsivo.
    righe = [f"📚 *{titolo(giorni).upper()}*"]
    diario = diario or {}
    nuovi = {str(x["giorno"]) for x in (diario.get("oggi"), diario.get("ieri")) if x}
    if diario.get("verifiche"):
        righe += ["", "⚠️ *VERIFICHE IN ARRIVO*"]
        righe += [f"• {GIORNI[d.weekday()].lower()} {d:%d/%m} ({tra_quanto(d, date.today())}): "
                  f"*{r['materia'] or 'Avviso'}*" for d, r in diario["verifiche"]]
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
                testo = pulisci(c["testo"])
                segni = ("📌" if c.get("fonte") == "agenda" else "") + ("🆕" if c.get("assegnato") in nuovi else "")
                righe.append(f"▪️ *{materia}*{' ' + segni if segni else ''}: {testo}")
        else:
            righe.append("▪️ Nessun compito registrato")
    # La data di aggiornamento SEMPRE in fondo: chi legge capisce subito se e' roba vecchia.
    if ricostruito and orario:
        righe += ["", f"_\u26a0\ufe0f {AVVISO_ORARIO}_"]
    righe += ["", "_📌 = scritto in Agenda · 🆕 = dato oggi o il giorno di scuola prima_",
              f"_Aggiornato il {datetime.now():%d/%m alle %H:%M} dal registro elettronico._",
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


def _blocco_diario(e, titolo, d):
    """Un giorno di scuola raccontato: le ore con l'argomento, le note in Agenda, i compiti dati."""
    out = [f"<h2>{titolo}</h2>"]
    if d["ore"]:
        out.append("<ul>")
        for o in d["ore"]:
            tipo = f" <em>({e(o['tipo'])})</em>" if o["tipo"] else ""
            arg = f": {e(o['argomento'])}" if o["argomento"] else ": <em>argomento non indicato</em>"
            out.append(f"<li>{o['ora']}ª <strong>{e(o['materia'])}</strong>{tipo}{arg}</li>")
        out.append("</ul>")
    else:
        out.append("<p>Nessuna lezione firmata sul registro (per ora).</p>")
    if d["note"]:
        out.append("<p><strong>Scritto in Agenda:</strong></p><ul>")
        out += [f"<li><strong>{e(n['materia'] or 'Avviso')}</strong>: {e(n['testo'])}</li>" for n in d["note"]]
        out.append("</ul>")
    if d["dati"]:
        out.append("<p><strong>Compiti dati:</strong></p><ul>")
        for c in d["dati"]:
            per = datetime.strptime(c["per"], "%Y-%m-%d").date() if c["per"] else None
            quando = f" <em>(per {GIORNI[per.weekday()].lower()} {per:%d/%m})</em>" if per else ""
            out.append(f"<li><strong>{e(c['materia'])}</strong>{quando}: {e(c['testo'])}</li>")
        out.append("</ul>")
    return out


def html_pagina_web(classe, orario, giorni, per_giorno, ricostruito=False, diario=None):
    """Il corpo della pagina: compiti in arrivo + orario della settimana."""
    # Pensata per essere condivisa (gruppo classe, stampa), quindi PRIVACY prima di tutto:
    # al massimo il nome della classe. Niente scuola, niente studenti, niente docenti.
    e = html.escape
    # Il nome della classe sta gia' nel titolo della pagina: qui solo la data, ben visibile.
    out = [f"<p><strong>Aggiornato il {datetime.now():%d/%m/%Y alle %H:%M}</strong></p>"]

    # diario = {"oggi": ..., "ieri": ..., "verifiche": [...]}: c'e' solo se il programma l'ha preparato.
    diario = diario or {}
    oggi_d, ieri_d = diario.get("oggi"), diario.get("ieri")
    nuovi = {str(x["giorno"]) for x in (oggi_d, ieri_d) if x}

    # 1. Le verifiche in arrivo, in cima: sono quelle che non si possono dimenticare.
    if diario.get("verifiche"):
        out.append("<h2>⚠️ Verifiche e interrogazioni in arrivo</h2><ul>")
        for d, r in diario["verifiche"]:
            quando = f"{GIORNI[d.weekday()].lower()} {d:%d/%m}, {tra_quanto(d, date.today())}"
            out.append(f"<li><strong>{e(quando)}</strong> · <strong>{e(r['materia'] or 'Avviso')}</strong>: "
                       f"{e(pulisci(r['testo']))}</li>")
        out.append("</ul>")

    # 2. Cosa hanno fatto in classe l'ultimo giorno di scuola.
    if oggi_d:
        g = oggi_d["giorno"]
        etichetta = "Oggi" if g == date.today() else GIORNI[g.weekday()]
        out += _blocco_diario(e, f"📖 {etichetta} in classe ({GIORNI[g.weekday()].lower()} {g:%d/%m})", oggi_d)

    # 3. I compiti, giorno per giorno: e' quello che il genitore cerca aprendo la pagina.
    out.append("<h2>📚 Compiti in arrivo</h2>")
    giorni_pieni = [g for g in giorni if per_giorno.get(str(g))]
    if not giorni_pieni:
        out.append("<p>Nessun compito registrato per i prossimi giorni.</p>")
    for g in giorni_pieni:
        # Il giorno deve SALTARE all'occhio: maiuscolo e grassetto.
        out.append(f"<h3><strong>{GIORNI[g.weekday()].upper()} {g:%d/%m}</strong></h3><ul>")
        for c in per_giorno[str(g)]:
            materia = e(c["materia"] or "Avviso")
            testo = e(pulisci(c["testo"]))
            nuovo = " 🆕" if c.get("assegnato") in nuovi else ""
            verifica = " ⚠️" if VERIFICA.search(c["testo"]) else ""
            agenda = " 📌" if c.get("fonte") == "agenda" else ""
            out.append(f"<li><strong>{materia}</strong>{agenda}{nuovo}{verifica}: {testo}</li>")
        out.append("</ul>")

    # 4. Il giorno di scuola prima: per chi era assente, o per chi vuole ripassare.
    if ieri_d:
        g = ieri_d["giorno"]
        out += _blocco_diario(e, f"🗓️ Il giorno prima ({GIORNI[g.weekday()].lower()} {g:%d/%m})", ieri_d)

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

    # La LEGENDA. Chi apre la pagina non ha letto il programma: i simboli vanno spiegati qui.
    out.append("<h2>Legenda</h2><ul>"
               "<li>⚠️ <strong>Verifiche e interrogazioni in arrivo</strong>: quelle dei prossimi 14 giorni, "
               "trovate cercando parole come verifica, interrogazione, compito in classe. "
               "Nell'elenco dei compiti il ⚠️ segna le stesse voci.</li>"
               "<li>📖 <strong>In classe</strong>: le lezioni dell'ultimo giorno di scuola, ora per ora, "
               "con l'argomento che il docente ha scritto sul registro. Sotto, le note scritte in Agenda "
               "quel giorno e i compiti dati quel giorno, con la data di consegna.</li>"
               "<li>📚 <strong>Compiti in arrivo</strong>: tutti i compiti già assegnati, "
               "divisi per giorno di CONSEGNA.</li>"
               "<li>📌 Compito scritto dal docente in <strong>Agenda</strong> invece che nella sezione "
               "Didattica del registro: nell'app è più facile non vederlo.</li>"
               "<li>🆕 Compito <strong>nuovo</strong>: dato oggi o il giorno di scuola prima.</li>"
               "<li>🗓️ <strong>Il giorno prima</strong>: lezioni e compiti del giorno di scuola precedente. "
               "Utile a chi era assente.</li>"
               "<li><em>(omesso)</em>: dove il docente aveva scritto nomi di alunni "
               "(per esempio «Interrogati: …»). Qui i nomi non si pubblicano.</li>"
               + ("<li>🕒 <strong>Orario settimanale</strong>: in fondo, solo se chiesto (--orario); "
                  "se è ricostruito dal registro può contenere errori.</li>" if orario else "")
               + "</ul>")
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


def pagina_completa(classe, orario, giorni, per_giorno, ricostruito=False, diario=None):
    """La pagina HTML finale: titolo, bottone Stampa, compiti in arrivo, orario della settimana."""
    titolo_pagina = f"Classe {classe}" if classe else "Compiti e orario"
    return (f"<!doctype html><html lang='it'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(titolo_pagina)}</title><style>{STILE_PAGINA}</style></head><body>"
            f"<h1>{html.escape(titolo_pagina)}</h1>"
            f"<button class='stampa' onclick='window.print()'>Stampa / salva PDF</button>"
            + html_pagina_web(classe, orario, giorni, per_giorno, ricostruito, diario) + "</body></html>")


# ================================================================ MAIN
# Il regista: chiede, scarica, mette in ordine, salva.

def main():
    # 1. Le opzioni. Senza niente: tutti i compiti in arrivo.
    ap = argparse.ArgumentParser(description="Compiti e orario da ClasseViva, pronti da leggere e stampare")
    ap.add_argument("--domani", action="store_true", help="solo il prossimo giorno di scuola")
    ap.add_argument("--data", help="un solo giorno, AAAA-MM-GG")
    ap.add_argument("--dal", help="inizio periodo, AAAA-MM-GG")
    ap.add_argument("--al", help="fine periodo, AAAA-MM-GG (default: uguale a --dal)")
    ap.add_argument("--sabato", action="store_true", help="la scuola fa lezione anche il sabato")
    ap.add_argument("--orario", action="store_true",
                    help="aggiungi in fondo l'orario della settimana (di base NO: ricostruito puo' sbagliare)")
    ap.add_argument("--uscita", default=".", help="cartella dove salvare i file (default: quella corrente)")
    ap.add_argument("--no-open", action="store_true", help="non aprire il foglio nel browser alla fine")
    ap.add_argument("--cambia-password", action="store_true",
                    help="richiede codice e password e aggiorna quelli salvati (es. dopo averla cambiata su ClasseViva)")
    ap.add_argument("--dimentica", action="store_true",
                    help="cancella codice e password salvati su questo computer, e basta")
    ap.add_argument("--debug", action="store_true",
                    help="salva le risposte grezze del server (contengono dati personali: NON condividerle)")
    a = ap.parse_args()
    if a.dimentica:
        print("[ok] credenziali cancellate da questo computer" if dimentica_credenziali()
              else "[i] su questo computer non c'erano credenziali salvate")
        return

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

    # 3. Le credenziali. Di base si chiedono ogni volta e NON si salvano.
    #    Se un giorno hai detto "s", stanno nel portachiavi del sistema e non le richiediamo.
    #    La password non compare mai sullo schermo, ne' mentre la scrivi ne' dopo.
    utente, password = (None, None) if a.cambia_password else credenziali_salvate()
    dal_portachiavi = bool(utente and password)
    if dal_portachiavi:
        print("[i] uso codice e password salvati su questo computer (per cambiarli: --cambia-password)")
    else:
        print("Accesso a ClasseViva")
        utente = input("  Codice utente o email del genitore: ").strip()
        password = getpass.getpass("  Password (non si vede mentre scrivi): ")
    cv = ClasseViva(utente, password, None, a.debug, "genitori")
    try:
        cv.accedi()
    except (SystemExit, Exception) as err:
        if dal_portachiavi:
            # Il caso tipico: la password e' stata cambiata (o e' scaduta) su ClasseViva.
            print("[!] Le credenziali salvate non funzionano piu'. Rilancia con:  --cambia-password")
        if isinstance(err, SystemExit):
            raise
        sys.exit(f"[!] Accesso non riuscito: {err}")
    print("[ok] accesso eseguito")
    # Solo DOPO un accesso riuscito si salva: una password sbagliata non la vogliamo ricordare.
    if a.cambia_password:
        if salva_credenziali(utente, password):
            print("[ok] codice e password aggiornati su questo computer")
    elif not dal_portachiavi and _portachiavi():
        r = input("  Vuoi che questo computer si ricordi codice e password? "
                  "Restano nel portachiavi del sistema. [s/N] ").strip().lower()
        if r in ("s", "si", "sì") and salva_credenziali(utente, password):
            print("[ok] salvati. Per toglierli:  --dimentica")
    password = None  # non la teniamo in giro piu' del necessario
    # La classe la dice il registro stesso: nessuno deve scriverla.
    # Le lezioni firmate dell'ultimo mese: le chiediamo UNA volta e servono a tre cose.
    # La classe (se il login non l'ha detta), chi insegna cosa (per le annotazioni) e l'orario.
    try:
        lezioni = cv.lezioni(date.today() - timedelta(weeks=4), date.today())
    except Exception:
        lezioni = []   # pazienza: il foglio esce lo stesso, con qualcosa in meno
    classe = cv.classe
    if not classe:
        # Con il login classico (genitori con piu' figli) il "chi sono" non c'e'.
        # Ma ogni lezione firmata riporta la classe.
        classe = classe_da_lezioni(lezioni)

    # 4. I compiti: Agenda + Didattica, raggruppati per giorno di consegna.
    # L'Agenda la chiediamo da 3 settimane fa: certe voci cominciano nel passato e
    # scadono nei prossimi giorni (vedi data_consegna), e servono le note di oggi e di ieri.
    docenti = materie_dei_docenti(lezioni)
    agenda = cv.agenda(oggi - timedelta(weeks=3), max(giorni[-1], oggi))
    didattica = cv.compiti_didattica()
    per_giorno = compiti_per_giorno(agenda, didattica, giorni, docenti)

    # Il diario: l'ultimo giorno di scuola (oggi, o venerdi' se e' domenica) e quello prima.
    diario = {"verifiche": verifiche_in_arrivo(per_giorno, oggi)}
    for chiave, g in zip(("oggi", "ieri"), giorni_con_lezioni(lezioni, oggi)[:2]):
        diario[chiave] = diario_del_giorno(g, lezioni, agenda, didattica, docenti)
    if tutti:
        giorni = [g for g in giorni if per_giorno.get(str(g))] or giorni[:1]

    # 5. L'orario. Solo se richiesto (--orario): ricostruito dal registro puo' sbagliare,
    #    e un orario sbagliato e' peggio di nessun orario. Lo zaino, i ragazzi, ormai lo sanno fare.
    #    Se c'e', orario.csv accanto al programma vince sempre sulla ricostruzione.
    csv = QUI / "orario.csv"
    if not a.orario:
        orario, origine = {}, ""
    elif csv.exists():
        orario, origine = orario_da_csv(csv), "da orario.csv"
    else:
        try:
            orario = orario_da_lezioni(lezioni, oggi)
            origine = "RICOSTRUITO in automatico: può contenere errori, fa fede l'orario ufficiale della scuola"
        except requests.HTTPError:
            orario, origine = {}, ""

    # 6. I file.
    uscita = Path(a.uscita).expanduser()
    uscita.mkdir(parents=True, exist_ok=True)
    # La classe nel nome del file: chi ha piu' figli lancia il programma una volta per figlio,
    # e con la sola data il secondo giro cancellerebbe i fogli del primo.
    # compiti_2A_2026-10-19.pdf, compiti_3C_2026-10-19.pdf: uno accanto all'altro.
    # (Due figli nella STESSA classe? Stesso nome, ma anche stessi compiti: nessun danno.)
    prefisso = f"compiti_{classe}_" if classe else "compiti_"
    nome = (f"{prefisso}{giorni[0]:%Y-%m-%d}" if len(giorni) == 1
            else f"{prefisso}{giorni[0]:%Y-%m-%d}_{giorni[-1]:%Y-%m-%d}")
    base = uscita / nome
    pagina = base.with_suffix(".html")
    ricostruito = bool(orario) and not csv.exists()
    pagina.write_text(pagina_completa(classe, orario, giorni, per_giorno, ricostruito, diario), encoding="utf-8")
    print(f"[ok] pagina  -> {pagina}")
    if genera_pdf(base.with_suffix(".pdf"), giorni, orario, origine, per_giorno,
                  f"Classe {classe}" if classe else ""):
        print(f"[ok] PDF     -> {base.with_suffix('.pdf')}")
    else:
        print("[i] per avere anche il PDF:  pip install reportlab  (intanto stampa la pagina)")
    base.with_suffix(".txt").write_text(testo_whatsapp(giorni, orario, per_giorno, ricostruito, diario),
                                        encoding="utf-8")
    print(f"[ok] testo per WhatsApp -> {base.with_suffix('.txt')}")
    if orario and not csv.exists():
        print("[i] l'orario e' ricostruito dal registro: se non torna, compila orario.csv (vedi il manuale)")
    if a.debug:
        print("[!] ATTENZIONE: i file debug_*.json contengono dati personali. Cancellali, non condividerli.")

    # 7. Apriamo la pagina, cosi' si vede subito il risultato.
    if not a.no_open:
        webbrowser.open(pagina.resolve().as_uri())


if __name__ == "__main__":
    main()
