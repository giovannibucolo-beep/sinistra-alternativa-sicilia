# Regole del sito

Regole fissate da Giovanni. Valgono per ogni pagina, presente e futura. Dove è possibile sono controllate in automatico a ogni pubblicazione.

## 1. Blocchi affiancati: stessa dimensione, stesso bordo inferiore
Quando più riquadri stanno sulla stessa fila (pilastri, schede delle notizie, i due binari, le province) hanno **tutti la stessa altezza** e sono **allineati sul bordo inferiore**, qualunque sia la lunghezza del testo.
*Regola del 26 novembre 2026. Controllo automatico: `strumenti/prova_resa.py`.*

## 2. «SA» è il simbolo
Quando si scrive «la Sicilia che SA…» o «la Sicilia SA…», la parola **SA non si scrive a lettere: è il monogramma**. Vale nei titoli, nelle fasce e nelle immagini di anteprima per i social. Il sito lo fa da solo: basta scrivere la frase normalmente nel titolo.
Su fondo chiaro il monogramma nero, su fondo nero quello in negativo, su fondo rosso quello tutto bianco.
Non vale dove un'immagine non può stare: il titolo nella scheda del browser, le descrizioni per i motori di ricerca, il testo corrente dei capoversi.
*Regola del 26 novembre 2026. Controllo automatico: `controlla.py`.*

## 3. Prima il telefono
Tasti grandi, almeno 44 px di altezza, nessuno scorrimento orizzontale. *Controllo automatico: `strumenti/prova_resa.py`.*

## 4. Apertura della home in una schermata
Su computer la prima sezione della home occupa esattamente una schermata. Le pagine interne scorrono.

## 5. Versione e data in fondo
Ogni pagina riporta nel piede «Versione X.Y · aggiornato il …». La versione aumenta a ogni pubblicazione; 1.0 è la prima approvata dal coordinamento.

## 6. Niente inventato senza etichetta
Contenuti dimostrativi con l'etichetta «esempio»; testi non approvati con `bozza: sì`, che li tiene fuori dal sito pubblico.

## 7. Identità
Nero di base, rosso SA (#EC3657) per accenti e pulsanti, cremisi (#B01030) per la Sicilia nel simbolo e per il testo rosso piccolo. Carattere Montserrat. I file del simbolo non si modificano.
