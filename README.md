# Compiti ClasseViva

L'app ClasseViva non mostra l'orario delle lezioni, e i compiti NON si possono stampare.
Questo piccolo programma li prende dal registro e prepara un foglio pulito: da leggere sul telefono, da stampare in A4, da incollare nel gruppo WhatsApp della classe.

**Manuali passo passo, per chi non ha mai usato un programma così:**
[Windows](MANUALE_WINDOWS.md) · [Mac](MANUALE_MAC.md) (anche in PDF, da stampare o girare su WhatsApp: [Windows](MANUALE_WINDOWS.pdf) · [Mac](MANUALE_MAC.pdf))

Ciao, sono un genitore come voi. L'ho fatto per i miei figli e lo condivido. Gratis, aperto, senza pubblicità.

## Cosa fa

1. Ti chiede codice utente e password ClasseViva del **genitore**.
   Se sull'account ci sono più figli, ti chiede di quale.
2. Scarica i compiti in arrivo (Agenda + Didattica) e li mette in ordine per giorno di consegna.
3. Aggiunge l'orario della settimana.
4. Prepara tre file:
   - una **pagina** da aprire nel browser, con il bottone "Stampa / salva PDF";
   - un **PDF** in A4;
   - un **testo per WhatsApp**, già formattato, senza nomi di nessuno.

## Privacy, prima di tutto

1. Le credenziali NON vengono salvate. Le scrivi ogni volta, e la password non compare sullo schermo.
2. Il programma parla SOLO con il server di Spaggiari. Non manda niente a nessun altro, nemmeno a me.
3. I fogli prodotti NON contengono nomi di studenti, docenti o scuola. Solo la sigla della classe (tipo "3B"), che il programma legge da solo dal registro.
4. Il codice è tutto qui, leggibile. Se non vi fidate, fatelo leggere a qualcuno di cui vi fidate. È giusto così.

## Attenzione: cosa NON è

- **NON è un prodotto Spaggiari**, né della scuola. Nessuno dei due lo ha approvato o lo supporta.
- Usa la stessa interfaccia **non ufficiale** usata dall'app ClasseViva, documentata da progetti open source ([open-viva/endpoints](https://github.com/open-viva/endpoints), [Classeviva.py](https://github.com/Lioydiano/Classeviva)). Se Spaggiari cambia qualcosa, il programma può smettere di funzionare da un giorno all'altro.
- Fa SOLO letture: non scrive, non giustifica, non modifica niente sul registro.
- Per i compiti, **fa fede il diario scritto a mano dall'alunno**: il programma è solo un aiuto in più.

## Installazione e uso

### Windows

1. Installa Python 3 da [python.org](https://www.python.org/downloads/). Durante l'installazione spunta **"Add python.exe to PATH"**.
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

Si può fare con app come a-Shell, ma è scomodo. Il consiglio onesto: lo fa girare un genitore dal computer e condivide il testo nel gruppo.

## Opzioni

```
compiti.sh                         tutti i compiti in arrivo + orario
compiti.sh --domani                solo il prossimo giorno di scuola
compiti.sh --data 2026-10-16       un giorno preciso
compiti.sh --dal 2026-10-19 --al 2026-10-23
compiti.sh --sabato                se la scuola fa lezione anche il sabato
```

Su Windows le opzioni si usano dal Prompt dei comandi: `AVVIA-WINDOWS.bat --domani`.

## L'orario

Il programma prova a **ricostruirlo** dalle lezioni firmate dai docenti nelle ultime settimane. Dove non è sicuro, lo dice con un punto interrogativo.

> ⚠️ **L'orario ricostruito PUÒ CONTENERE ERRORI.** Fa fede l'orario ufficiale comunicato dalla scuola.
> Sbaglia soprattutto quando lo stesso docente insegna più materie (per esempio Matematica e Scienze, o Italiano, Storia e Geografia), quando ci sono supplenze o compresenze, e a inizio anno, quando l'orario è ancora provvisorio. Per questo, ogni volta che l'orario è ricostruito, la pagina, il PDF e il testo per WhatsApp lo dicono chiaramente.

Se volete l'orario giusto al 100%, scrivetelo una volta sola:

1. copiate `orario.csv.esempio` come `orario.csv`, nella stessa cartella;
2. una riga per ogni ora: `giorno;ora;materia` (1 = lunedì ... 5 = venerdì);
3. da lì in poi il programma usa quello.

Un consiglio: uno lo compila, e lo gira agli altri genitori della classe.

## Aggiornare

Quando esce una versione nuova: si cancella la vecchia cartella (salvando prima `orario.csv`, se c'è) e si riscarica lo ZIP. Python non va reinstallato. I manuali spiegano i passi.

## Se qualcosa non va

1. **"Accesso non riuscito"**: controlla codice utente e password provando ad entrare dal sito ClasseViva.
2. **Mancano dei compiti**: alcuni docenti li scrivono come semplice nota in Agenda. Il programma li mostra come "Avviso".
3. **Errore strano dal server**: lancia con `--debug`. Salva le risposte del server in file `debug_*.json`.
   **ATTENZIONE**: quei file contengono dati personali (anche il codice fiscale). Guardali, poi cancellali. NON mandarli a nessuno.

## Chi l'ha fatto

Francesco, **Executive Senior Chief Global Cybersecurity Officer of Compiti, Orari & Zaini**.
Tradotto: un papà che di giorno si occupa di sicurezza informatica e la sera combatte con il registro elettronico come tutti.

Racconto la sicurezza digitale in forma di storie sul blog [Cronache del Sottosopra](https://www.cronachesottosopra.it/articoli/), da cui è nato anche un libro. Il programma invece resta gratuito, per sempre.

## Licenza

GPL-3.0: potete usarlo, studiarlo, modificarlo e ridistribuirlo, a patto che le versioni modificate restino libere allo stesso modo.

Nessuna garanzia: lo uso per i miei figli, funziona per noi, ma non posso promettere che funzioni per tutti e per sempre.

Ciao / Francesco

PS: se lo migliorate, mandatemi le modifiche. Qui su GitHub si chiama "pull request".
