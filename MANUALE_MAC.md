# Compiti ClasseViva: manuale per Mac

Questo manuale ti accompagna passo passo. Non serve saper usare il computer più di tanto: basta seguire i passi nell'ordine, senza saltarne nessuno.

Tempo necessario: **circa 10 minuti la prima volta**. Le volte successive: **una riga da incollare**.

## Cosa ti serve

- Un **Mac** abbastanza recente (macOS 11 o successivo).
- Il **codice utente** (o l'email) e la **password** che usi per entrare in ClasseViva come genitore.

---

## PARTE 1. Controllare Python (una volta sola)

Python è il "motore" che fa funzionare il programma. È gratuito e sicuro. Spesso sul Mac **c'è già**: controlliamo.

1. Apri il **Terminale**: premi insieme i tasti **Cmd** e **Barra spaziatrice**, scrivi **Terminale** e premi **Invio**.
    Si apre una finestra con del testo. Non spaventarti: è normale, e non puoi rompere niente.

2. **Copia** questa riga (selezionala e premi **Cmd + C**), poi clicca nella finestra del Terminale, **incolla** con **Cmd + V** e premi **Invio**:

    ```
    python3 --version
    ```

3. Ora guarda cosa succede. Può succedere **una di queste tre cose**:

    - **A. Compare una scritta tipo "Python 3.9.6"** (il numero non importa).
      Perfetto, Python c'è già. **Salta alla PARTE 2.**

    - **B. Compare una finestra che chiede di installare gli "strumenti per sviluppatori da riga di comando".**
      Clicca **Installa**, poi **Accetta**. Aspetta che finisca: può volerci **qualche minuto, anche dieci**. Quando ha finito, clicca **Fine**.
      Python adesso c'è. **Vai alla PARTE 2.**

    - **C. Compare un errore, oppure non succede niente.**
      Nessun problema, lo installiamo a mano:
        1. apri **Safari** e vai su **www.python.org/downloads**;
        2. clicca il grande bottone giallo **Download Python 3...**;
        3. apri la cartella **Download** e fai doppio clic sul file che finisce con **.pkg**;
        4. clicca **Continua** a ogni schermata, poi **Accetta**, poi **Installa**;
        5. il Mac chiede la **password del Mac** (quella con cui accendi il computer): scrivila e premi Invio;
        6. alla fine clicca **Chiudi**.

Il Terminale per ora puoi lasciarlo aperto: ti serve di nuovo tra poco.

---

## PARTE 2. Scaricare il programma (una volta sola)

1. Vai su: **github.com/FRitrovato/compiti-classeviva**
2. Clicca il bottone verde **<> Code**.
3. Nel menu che si apre, clicca **Download ZIP**.
4. Apri la cartella **Download** (dal Finder, nella colonna a sinistra).
    - Con **Safari** trovi già una cartella **compiti-classeviva-main**.
    - Con **Chrome** trovi un file **compiti-classeviva-main.zip**: fai doppio clic e diventa una cartella.
5. **Trascina la cartella compiti-classeviva-main sulla Scrivania.**
    È importante: le istruzioni qui sotto la cercano proprio lì.

---

## PARTE 3. Usarlo

Sul Mac si usa il **Terminale**, una finestra dove si scrivono comandi. Sembra da esperti, ma ti basta copiare e incollare **una sola riga**.

1. Se l'hai chiuso, riapri il **Terminale**: **Cmd** + **Barra spaziatrice**, scrivi **Terminale**, **Invio**.

2. **Copia** questa riga (selezionala e premi **Cmd + C**):

    ```
    bash ~/Desktop/compiti-classeviva-main/compiti.sh
    ```

3. Clicca dentro la finestra del Terminale, **incolla** con **Cmd + V** e premi **Invio**.

4. **La prima volta** scrive "Prima volta: preparo l'ambiente Python..." e ci mette uno o due minuti. Aspetta senza chiudere niente.

5. Quando vedi la scritta **Codice utente o email del genitore:**
    scrivi il codice che usi per ClasseViva (per esempio G1234567X, oppure la tua email) e premi **Invio**.

6. Quando vedi **Password:**
    scrivi la password e premi **Invio**.
    **ATTENZIONE:** mentre scrivi la password NON compare niente, nemmeno gli asterischi. È voluto, per sicurezza. Scrivi lo stesso e premi Invio.

7. Dopo qualche secondo si apre **Safari** con il foglio:
    - in alto, i **compiti in arrivo**, giorno per giorno;
    - in basso, l'**orario della settimana**;
    - il bottone blu **Stampa / salva PDF** per stamparlo.

8. Il Terminale lo puoi chiudere (**Cmd + Q**).

**Le credenziali non vengono salvate:** le scrivi ogni volta. È più sicuro così.

---

## Le volte successive

Solo la **PARTE 3**: apri il Terminale, incolla la stessa riga, codice, password, ecco il foglio. Niente installazioni.

**Trucco:** nel Terminale, premendo la **freccia in su** ricompare l'ultima riga che hai usato. Premi Invio e sei a posto.

---

## Dove finiscono i fogli

Nella cartella **compiti-classeviva-main** sulla Scrivania trovi tre file nuovi ogni volta, con la data nel nome:

- **compiti_....html**: la pagina da aprire nel browser (doppio clic);
- **compiti_....pdf**: pronto da stampare o da mandare;
- **compiti_....txt**: il testo da copiare e incollare nel gruppo WhatsApp della classe.

---

## Se qualcosa non va

| Cosa succede | Cosa fare |
|---|---|
| **"No such file or directory"** | La cartella non è sulla Scrivania, oppure ha un altro nome. Controlla che sulla Scrivania ci sia proprio **compiti-classeviva-main**. |
| **"Manca Python 3"**, oppure compare la finestra degli **strumenti per sviluppatori** | Torna alla PARTE 1 e segui il caso B o C. Poi riprova. |
| **"Accesso non riuscito"** | Codice o password sbagliati. Prova a entrare dal sito di ClasseViva con gli stessi dati: se lì funziona, riprova qui facendo attenzione a maiuscole e minuscole. |
| **Errore con la parola "certificate"** | Apri **Applicazioni** > cartella **Python 3...** > doppio clic su **Install Certificates.command**. Poi riprova. |
| **L'orario è sbagliato** | Il programma lo ricostruisce dal registro e a volte sbaglia. Chiedi in classe se qualcuno ha già il file **orario.csv** giusto e mettilo nella cartella del programma. |
| **Mancano dei compiti** | Alcuni docenti li scrivono come nota: compaiono come **Avviso**. In caso di dubbio, fa fede il registro. |

---

## Da sapere

- Il programma **legge** soltanto: non modifica niente sul registro.
- Parla solo con il server di ClasseViva, non manda i tuoi dati a nessun altro.
- **Non è un prodotto Spaggiari né della scuola**: l'ha fatto un genitore, gratis. Se un giorno smette di funzionare, è perché Spaggiari ha cambiato qualcosa.

Ciao / Francesco
