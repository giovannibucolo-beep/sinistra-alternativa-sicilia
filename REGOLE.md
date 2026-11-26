# Regole del sito

Regole fissate da Giovanni. Valgono per ogni pagina, presente e futura. Dove è possibile sono controllate in automatico a ogni pubblicazione.

## 1. Blocchi affiancati: stessa dimensione, stesso bordo inferiore
Quando più riquadri stanno sulla stessa fila (pilastri, schede delle notizie, i due binari, le province) hanno **tutti la stessa altezza** e sono **allineati sul bordo inferiore**, qualunque sia la lunghezza del testo.
*Regola del 26 novembre 2026. Controllo automatico: `strumenti/prova_resa.py`.*

## 2. «SA» è il simbolo
Quando si scrive «la Sicilia che SA…» o «la Sicilia SA…», la parola **SA non si scrive a lettere: è il monogramma**. Vale nei titoli, nelle fasce e nelle immagini di anteprima per i social. Il sito lo fa da solo: basta scrivere la frase normalmente nel titolo.
Il simbolo non va mai a capo da solo: resta sulla stessa riga della parola che lo precede.
Su fondo chiaro il monogramma nero, su fondo nero quello in negativo, su fondo rosso quello tutto bianco.
Non vale dove un'immagine non può stare: il titolo nella scheda del browser, le descrizioni per i motori di ricerca, il testo corrente dei capoversi.
*Regola del 26 novembre 2026. Controllo automatico: `controlla.py`.*

## 3. Prima il telefono
Tasti grandi, almeno 44 px di altezza, nessuno scorrimento orizzontale. *Controllo automatico: `strumenti/prova_resa.py`.*

## 4. Blocchi uniformi per schermata, nessun blocco tagliato
Su computer **ogni pagina è fatta di blocchi grandi esattamente quanto lo schermo**, e la pagina si ferma sempre su un blocco intero: non si vede mai un riquadro tagliato a metà. Il contenuto di ogni blocco deve starci tutto: se è troppo, si divide in più schermate (tre notizie per schermata, quattro incontri per schermata).
Anche il piede è una schermata.
Eccezioni dichiarate, dove il testo ha lunghezza libera: il corpo di una notizia e la pagina «Tutto in una pagina», fatta per la stampa.
Su telefono i blocchi stanno in colonna, uno sotto l'altro, e la pagina scorre.
*Regola del 26 novembre 2026 (riprende quella della pagina unica). Controllo automatico: `strumenti/prova_schermate.py`, a quattro misure di schermo.*

## 5. Versione e data in fondo
Ogni pagina riporta nel piede «Versione X.Y · aggiornato il …». La versione aumenta a ogni pubblicazione; 1.0 è la prima approvata dal coordinamento.

## 6. Niente inventato senza etichetta
Contenuti dimostrativi con l'etichetta «esempio»; testi non approvati con `bozza: sì`, che li tiene fuori dal sito pubblico.

## 7. Identità
Nero di base, rosso SA (#EC3657) per accenti e pulsanti, cremisi (#B01030) per la Sicilia nel simbolo e per il testo rosso piccolo. Carattere Montserrat. I file del simbolo non si modificano.

## 8. Fotografie
- Ogni pilastro ha una fotografia **mirata al suo tema** (MUOS, ospedale di un’area interna, Stretto…), non un’immagine generica.
- Solo fotografie con licenza libera (Wikimedia Commons: dominio pubblico, CC0, CC BY, CC BY-SA) o nostre. Elenco in `contenuti/foto.json`.
- Sotto ogni foto: soggetto, autore, licenza. Tutti i dettagli nella pagina «Crediti fotografici».
- Niente volti riconoscibili di persone estranee al coordinamento; niente opere d’arte di autori viventi.
- **Sempre ottimizzate per il web, qualunque formato abbiano**: si mette il file in `risorse/img/` (JPEG, PNG, HEIC, WebP, TIFF…) e il sito lo trasforma da solo in JPEG progressivo largo al massimo 1400 px, sotto i 350 KB, senza dati incorporati (posizione, apparecchio). Il controllo blocca la pubblicazione se una foto pesa di più.
- L’elenco dei crediti fotografici cresce con le foto: come il testo di una notizia, è un’eccezione alla regola 4 e scorre libero.

## 9. Cookie e statistiche
- Il sito nasce senza cookie. Gli strumenti di misura si accendono scrivendo il loro codice in `contenuti/sito.json`, voce `statistiche`.
- Quelli con cookie (Google Analytics, pixel di Meta) partono solo dopo il consenso; «Rifiuta» e «Accetta tutto» hanno lo stesso peso, la × vale rifiuto, la scelta dura sei mesi e si cambia dalla pagina «Cookie».
- La pagina «Cookie» si scrive da sola in base a ciò che è acceso: non va mai modificata a mano. Come il testo di una notizia, scorre libera.
