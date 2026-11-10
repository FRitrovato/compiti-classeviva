# Compiti ClasseViva

Ore 21:30, cucina, scena nota a tutti:

> «Hai fatto i compiti?» «Sì.» «Quali?» «Boh, non c'erano.» «E oggi in classe cosa avete fatto?» «Niente.»

Ecco, questo programma esiste per quella scena.

L'app ClasseViva i compiti li ha, ma **sparsi tra Agenda e Didattica**, e **NON si possono stampare**. Questo programmino li prende dal registro e prepara un foglio pulito: da leggere sul telefono, da stampare in A4, da incollare nel gruppo WhatsApp della classe. E ci aggiunge quello che l'app non ti dice.

**Manuali passo passo, per chi non ha mai aperto un Terminale (e ne va fiero):**
[Windows](MANUALE_WINDOWS.md) · [Mac](MANUALE_MAC.md) (anche in PDF, da stampare o girare su WhatsApp: [Windows](MANUALE_WINDOWS.pdf) · [Mac](MANUALE_MAC.pdf))

Ciao, sono un genitore come voi. L'ho fatto per i miei figli e lo condivido. Gratis, aperto, senza pubblicità. Senza abbonamento "premium" a 4,99 al mese, giuro.

## Cosa fa

1. Ti chiede codice utente e password ClasseViva del **GENITORE**. Se sull'account ci sono più figli, ti chiede di quale.
2. Mette in **cima le verifiche e le interrogazioni** dei prossimi 14 giorni ⚠️, con il conto alla rovescia: «tra 2 giorni». Perché la frase «ma la verifica è DOMANI?!» la sera tardi non deve più esistere.
3. Racconta **cosa hanno fatto IN CLASSE** 📖: le lezioni dell'ultimo giorno di scuola, ora per ora, con l'argomento scritto dal docente. Addio «niente».
4. Elenca **tutti i compiti in arrivo** 📚, in fila per giorno di consegna, con due segni:
   - 📌 = scritto dal docente in **Agenda** invece che in Didattica: nell'app sono quelli che si perdono;
   - 🆕 = dato **oggi** o il giorno di scuola prima.
5. Racconta anche **il giorno prima** 🗓️: lezioni e compiti. Per chi era a casa con la febbre (o «con la febbre»).
6. In fondo, una **legenda**: ogni simbolo spiegato, così nessuno deve chiedere niente a nessuno.
7. Prepara tre file:
   - una **pagina** da aprire nel browser, con il bottone "Stampa / salva PDF";
   - un **PDF** in A4;
   - un **testo per WhatsApp**, già formattato, senza nomi di nessuno.

E l'orario? **Solo se lo chiedi**, con `--orario`. Più sotto il perché.

## Privacy, prima di tutto

1. Di base le credenziali **NON vengono salvate**: le scrivi ogni volta, e la password non compare sullo schermo nemmeno con gli asterischi.
   Se ti scoccia riscriverla, dopo il primo accesso il programma ti chiede se vuoi farla ricordare al computer. Rispondi **s** e finisce nel **portachiavi del sistema** (Portachiavi su Mac, Gestione credenziali su Windows): lo stesso posto dove il computer tiene le altre password. **MAI in un file.**
   Si cambia con `--cambia-password`, si cancella con `--dimentica`.
2. Il programma parla SOLO con il server di Spaggiari. Non manda niente a nessun altro. Nemmeno a me. Soprattutto a me.
3. I fogli NON contengono nomi di studenti, docenti o scuola. Solo la sigla della classe (tipo "3B"), che il programma legge da solo.
   Se un docente scrive sul registro «Interrogati: Rossi, Bianchi», sul foglio esce «Interrogati: (omesso)». Le ore di sostegno non compaiono: riguardano un alunno, non la classe.
4. Il codice è tutto qui, leggibile. Se non vi fidate, fatelo leggere a qualcuno di cui vi fidate. È giusto così, anzi: è proprio così che si fa.

## Attenzione: cosa NON è

- **NON è un prodotto Spaggiari**, né della scuola. Nessuno dei due lo ha approvato o lo supporta. Se vi lamentate con loro, vi guarderanno strano.
- Usa la stessa interfaccia **non ufficiale** usata dall'app ClasseViva, documentata da progetti open source ([open-viva/endpoints](https://github.com/open-viva/endpoints), [Classeviva.py](https://github.com/Lioydiano/Classeviva)). Se Spaggiari cambia qualcosa, il programma può smettere di funzionare da un giorno all'altro.
- Fa SOLO letture: non scrive, non giustifica, non modifica niente sul registro. No, non può cambiare i voti. Ci avete pensato, lo so.
- Per i compiti **fa fede il diario scritto a mano dall'alunno**. Il programma è solo un alleato.

## Installazione e uso

### Windows

1. Installa Python 3 da [python.org](https://www.python.org/downloads/). Durante l'installazione spunta **"Add python.exe to PATH"**. Quella spunta è il 90% del successo.
2. Scarica questo progetto (bottone verde **Code** > **Download ZIP**) ed estrailo in una cartella.
3. Doppio clic su **`AVVIA-WINDOWS`**.

La prima volta ci mette un minuto a prepararsi. Poi chiede le credenziali e apre il foglio nel browser.

### Mac e Linux

1. Python 3 di solito c'è già. Se manca: [python.org](https://www.python.org/downloads/).
2. Scarica il progetto ed estrailo.
3. Sposta la cartella sulla Scrivania, apri il Terminale e scrivi:

```
bash ~/Desktop/compiti-classeviva-main/compiti.sh
```

### Android (per chi se la cava)

1. Installa l'app gratuita **Pydroid 3** dal Play Store.
2. Dal menu di Pydroid: **Pip** > installa `requests` e `reportlab`.
3. Apri `compiti_classeviva.py` e premi il tasto "play".
4. I file vengono salvati nella cartella da cui l'hai aperto.

### iPhone

Si può fare con app come a-Shell, ma è scomodo. Il consiglio onesto: lo fa girare un genitore dal computer e condivide il testo nel gruppo. Si chiama solidarietà.

## Opzioni

```
compiti.sh                         tutti i compiti in arrivo (il caso di tutti i giorni)
compiti.sh --domani                solo il prossimo giorno di scuola
compiti.sh --data 2026-10-16       un giorno preciso
compiti.sh --dal 2026-10-19 --al 2026-10-23
compiti.sh --orario                aggiungi in fondo l'orario della settimana
compiti.sh --sabato                se la scuola fa lezione anche il sabato
compiti.sh --cambia-password       nuova password (sostituisce quella salvata)
compiti.sh --dimentica             cancella codice e password salvati sul computer
```

Su Windows le opzioni si usano dal Prompt dei comandi: `AVVIA-WINDOWS.bat --domani`. I manuali spiegano come aprirlo senza paura.

## L'orario (solo se lo chiedi)

Di base **l'orario NON c'è**. Il motivo è semplice: l'app non lo dà, quindi il programma lo **ricostruisce** dalle lezioni firmate dai docenti. E un orario ricostruito **PUÒ CONTENERE ERRORI**: sbaglia soprattutto quando lo stesso docente insegna più materie (Matematica e Scienze, Italiano, Storia e Geografia), con supplenze e compresenze, e a inizio anno quando l'orario è ancora provvisorio.

Un orario sbagliato è peggio di nessun orario: porti in classe il libro sbagliato con la massima sicurezza. Quindi lo mostriamo solo a chi lo vuole:

```
compiti.sh --orario
```

Dove il programma non è sicuro, mette un punto interrogativo. E ogni volta che l'orario è ricostruito, pagina, PDF e testo per WhatsApp lo dicono chiaramente. **Fa fede l'orario ufficiale della scuola.**

Volete l'orario giusto al 100%? Scrivetelo una volta sola:

1. copiate `orario.csv.esempio` come `orario.csv`, nella stessa cartella;
2. una riga per ogni ora: `giorno;ora;materia` (1 = lunedì ... 5 = venerdì);
3. da lì in poi, con `--orario`, il programma usa quello.

Un consiglio: uno lo compila, e lo gira agli altri genitori della classe. Un caffè offerto al rappresentante di classe e il gioco è fatto.

## Aggiornare

Quando esce una versione nuova: si cancella la vecchia cartella (salvando prima `orario.csv`, se c'è) e si riscarica lo ZIP. Python non va reinstallato, e la password salvata resta dov'era. I manuali spiegano i passi.

## Se qualcosa non va

1. **"Accesso non riuscito"**: controlla codice utente e password provando a entrare dal sito ClasseViva. Se entri con SPID, sappi che qui serve codice e password: si impostano dal sito con "Password dimenticata".
2. **"Le credenziali salvate non funzionano più"**: hai cambiato la password su ClasseViva (o te l'ha fatta cambiare lui). Rilancia con `--cambia-password`.
3. **Mancano dei compiti**: alcuni docenti li scrivono come nota in Agenda. Il programma li mostra con lo 📌.
4. **Errore strano dal server**: lancia con `--debug`. Salva le risposte del server in file `debug_*.json`.
   **ATTENZIONE**: quei file contengono dati personali (anche il codice fiscale). Guardali, poi cancellali. NON mandarli a nessuno. Nemmeno a me.

## Chi l'ha fatto

Francesco, **Executive Senior Chief Global Cybersecurity Officer of Compiti, Orari & Zaini**.
Tradotto: un papà che di giorno si occupa di sicurezza informatica e la sera combatte con il registro elettronico come tutti.

Racconto la sicurezza digitale in forma di storie sul blog [Cronache del Sottosopra](https://www.cronachesottosopra.it/articoli/), da cui è nato anche [un libro](https://www.cronachesottosopra.it/). Il programma invece resta gratuito, per sempre.

## Licenza

GPL-3.0: potete usarlo, studiarlo, modificarlo e ridistribuirlo, a patto che le versioni modificate restino libere allo stesso modo.

Nessuna garanzia: lo uso per i miei figli, funziona per noi, ma non posso promettere che funzioni per tutti e per sempre. E no, non fa i compiti al posto loro.

Ciao / Francesco

PS: se lo migliorate, mandatemi le modifiche. Qui su GitHub si chiama "pull request". Suona complicato, è gentilezza.
