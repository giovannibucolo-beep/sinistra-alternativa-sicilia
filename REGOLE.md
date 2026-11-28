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

## 10. Privacy e note legali
- I nomi e i dati di chi risponde stanno in `contenuti/sito.json`, voce `legale` (più `contatti` e `committente`): si scrivono una volta e compaiono in tutte e due le pagine. Finché mancano, le pagine mostrano «da indicare».
- Le due pagine scorrono libere, come il testo di una notizia.
- Restano «Bozza da approvare» finché chi segue i dati per il coordinamento non le ha lette.

## 11. Materiali e condivisione
- I materiali scaricabili si elencano in `contenuti/materiali.json` e i file vanno in `risorse/materiali/`. Un materiale elencato ma non ancora caricato compare come «in preparazione»: l'elenco non mente mai.
- Ogni notizia e ogni pilastro hanno i pulsanti per condividere (WhatsApp, Telegram, Facebook, email, copia il link). Sono solo collegamenti: nessuno script di terze parti, nessun cookie.
- Volantino e manifesto si rifanno con `stampa/costruisci_stampa.py`: leggono i pilastri dagli stessi file del sito, così carta e sito non divergono mai. Il codice QR punta alla pagina di adesione e si rigenera da solo.
- Su ogni materiale stampato va il committente responsabile: finché non è indicato in `sito.json`, i PDF riportano «COMMITTENTE RESPONSABILE DA INDICARE» bene in vista, così nessuno li manda in tipografia per sbaglio.
- Le intestazioni dei file di contenuto devono essere YAML valido: un valore che contiene «: » va fra virgolette. Non è una finezza — è ciò che permette al pannello di scrittura di vedere il file. Il controllo blocca la pubblicazione se un'intestazione non si legge.

## 12. Sicurezza
- Ogni pagina dichiara che cosa può caricare: solo roba nostra. Niente stili né script scritti dentro il codice della pagina: se servono, vanno nel foglio di stile o in `risorse/sito.js`. Il motivo non è formale — è quella regola che impedisce a un testo malevolo di diventare codice eseguito.
- Il programma del pannello di scrittura è bloccato a una versione precisa, con la sua impronta: se il file cambia di un byte, il browser lo rifiuta. Per aggiornarlo si cambia versione, si ricalcola l'impronta, si prova e si pubblica.
- Le azioni della pubblicazione automatica sono bloccate a una versione precisa (SHA), non a un'etichetta che altri possono spostare.
- `/.well-known/security.txt` dice a chi scrivere per segnalare un problema.

## 13. Movimento e immagini
- Di ogni fotografia escono due misure: la grande da 1400 px e la piccola da 700 px. È il browser a scegliere; il telefono scarica la piccola. Le copie piccole le fa `strumenti/ottimizza_foto.py` da sé: non si creano a mano.
- I numeri in evidenza si scrivono nel contenuto con `= numero | che cosa dice | da dove viene`, e il numero per intero sta già nella pagina. Il conteggio che sale è solo un ornamento: senza JavaScript, e per chi ha chiesto meno animazioni, il numero si vede fermo e giusto. Ogni numero porta la sua fonte: nessun numero senza fonte.
- Il movimento ammesso è uno solo: il contenuto che entra di venti pixel allo scorrimento. Niente video di sfondo, niente parallasse, niente transizioni fra pagine.

## 14. Icone
- Le icone sono nostre, disegnate nel generatore (`ICONE` in `costruisci.py`): dicono il gesto — bolla, invio, globo, busta, catena — non il marchio. I loghi di WhatsApp, Telegram, Facebook e di qualunque altro servizio sono marchi registrati: non si riproducono, nemmeno ridisegnati «somiglianti».
- Accanto all'icona resta sempre il nome scritto. Sotto i 520 px il nome resta nel codice per chi usa il lettore di schermo, anche quando non si vede.

## 15. Loghi dei servizi di condivisione
- La cartella `risorse/loghi/servizi/` è il solo posto dove possono stare i loghi veri di WhatsApp, Telegram e Facebook. Se c'è `whatsapp.svg`, `telegram.svg` o `facebook.svg`, il sito lo usa da sé al posto del proprio pittogramma; se manca, resta il pittogramma.
- Va messa solo la versione a un colore: il sito usa il file come sagoma e gli dà il colore del pulsante, così diventa bianco sul fondo nero come le altre icone. Un file a colori diventa una macchia piena.
- I loghi si scaricano dalle pagine ufficiali dei marchi, mai da raccolte di icone di terze parti, e non si ridisegnano «somiglianti». Sono marchi registrati: chi li mette si è letto le condizioni d'uso e se ne assume la responsabilità. Le istruzioni stanno in `risorse/loghi/servizi/LEGGIMI.md`.

## 16. Niente sopratitoli decorativi
- Sopra un titolo non va la micro-etichetta maiuscola a lettere spaziate quando ripete quello che il titolo, la briciola o il menù dicono già. È la cosa che fa sembrare tutte le pagine uguali e fatte a stampo.
- Il sopratitolo resta solo dove porta un dato che non c'è altrove: «Prossimo incontro», «In provincia di ‹nome›», il tipo e il peso di un materiale, i due binari.
- Dove il numero conta — i pilastri — il numero è grande, rosso, da manifesto (`.ordinale`), non un sopratitolo.

## 17. Crediti fotografici
- Sulla fotografia non va più la banda nera con l'autore. L'attribuzione che le licenze chiedono sta tutta in `crediti.html`, raggiungibile dal piede di ogni pagina.
- Ogni voce dei crediti deve avere quattro cose: il soggetto, che è un collegamento alla fotografia stessa; l'autore con l'anno; la licenza, con collegamento al testo della licenza; l'originale su Wikimedia Commons. E la pagina in cui la foto compare, così dal credito si risale alla foto e viceversa.
- Se una fotografia è registrata in `foto.json` ma non compare in nessuna pagina, la costruzione lo stampa e i crediti lo scrivono: «Non usata in nessuna pagina». Non si lascia così.

## 18. Niente doppioni fra barra e piede
- Nel piede non si ripete quello che sta già nella barra in cima, che è sempre visibile. Il piede porta solo quello che la barra non ha: le pagine di servizio, i contatti per esteso, i canali, le note legali.
- Chi aggiunge una voce alla barra la toglie dal piede, e viceversa. La prova è meccanica: l'elenco dei collegamenti della barra e quello del piede non devono avere nessun indirizzo in comune.

## 19. Una sezione scritta deve comparire in pagina
- Se qualcuno scrive una sezione in un contenuto, quella sezione va mostrata. Il modello di «Chi siamo» ne mostrava solo tre e buttava via il resto senza dire niente: chi scriveva dal pannello non se ne accorgeva.
- Ora ogni sezione diventa una schermata nell'ordine in cui è scritta, e la costruzione si ferma con un errore se una sezione non finisce in pagina. Lo stesso vale per qualunque modello si aggiunga in futuro: o mostra tutto, o si ferma.
- Una sezione lunga (oltre 700 caratteri) non entra in una schermata intera: va a scorrimento libero. Se no il testo si taglia, e la prova delle schermate lo segnala.

## 20. Niente contenuti di esempio sul sito pubblicato
- Un contenuto inventato per far vedere come sarà la pagina si marca `bozza: sì`: resta nel pannello come modello e non esce sul sito. L'etichetta «esempio» non si usa più per i contenuti pubblicati.
- Un dato che non c'è si lascia **vuoto**, non si riempie con un segnaposto. Contatti, referenti e recapiti vuoti non vengono mostrati da nessuna parte: meglio niente che un'email finta scambiata per vera.
- Il passaggio alla versione definitiva è una riga sola, `bozza: false` in `contenuti/sito.json`, e la costruzione si ferma se mancano i dati veri: email di contatto, committente responsabile, i cinque campi dell'informativa, l'indirizzo del servizio che riceve le adesioni. Non si pubblica come definitivo un sito con i contatti vuoti.

## 21. Segnaposto nel calendario
- Ogni incontro futuro produce da sé il suo file per il calendario (`agenda/<file>.ics`), con l'avviso il giorno prima. Non si scrive a mano.
- Il segnaposto compare in due posti: l'icona del calendario accanto alla riga dell'agenda, e sulla pagina dell'incontro il pulsante «Salva nel calendario» più il collegamento a Google Calendar.
- Il collegamento a Google è solo un collegamento: non carica niente di Google dentro il sito e non lascia cookie finché qualcuno non lo clicca. Per chi non usa Google basta il file, che vale su telefono, Mac, Windows e Outlook.

## 22. Etichetta «bozza» e avvisi veri sono due cose diverse
- L'etichetta grande nell'angolo (`avviso_bozza`) è un interruttore a sé: si spegne quando sul sito non c'è più nulla di finto. `bozza` invece resta vero finché il coordinamento non approva la versione 1.0, e tiene in piedi la guardia che blocca un definitivo incompleto.
- Gli avvisi precisi non dipendono da quell'interruttore e compaiono da soli finché sono veri: il modulo che non è collegato, l'informativa con voci ancora «da indicare», il programma in attesa del voto. Spariscono da soli quando la cosa è stata fatta.
- Non si toglie un avviso perché è antipatico: si toglie risolvendo quello che l'avviso dice.

## 23. Stampa e PDF
- Niente comandi scritti dentro i tag (`onclick` e simili): le regole di sicurezza della pagina li bloccano e il pulsante non fa niente. Il comando va in `risorse/sito.js`, agganciato a un attributo come `data-stampa`.
- La pagina `programma/tutto.html` contiene **tutte** le sezioni di ogni pilastro. Era tagliata alle prime due e il PDF usciva senza i binari dello Stato né le obiezioni.
- In stampa ogni pilastro comincia su una pagina nuova, i titoli non restano soli in fondo al foglio, elenchi e capoversi non si spezzano. Barra, piede, briciole, punti di scorrimento e pulsanti spariscono.
- Dopo ogni modifica al programma la stampa va riprovata davvero generando il PDF, non guardando la pagina a schermo.

## 24. Carta intestata della stampa
- Il foglio stampato porta il contrassegno, il nome del coordinamento, «Elezioni regionali 2027», il titolo del documento e la data del giorno, con una riga rossa sotto. In fondo a ogni pagina il nome e l'indirizzo del sito. Tutto questo **si vede solo in stampa**: a schermo è nascosto.
- Il simbolo nella carta intestata è il contrassegno (`sa-contrassegno.svg`), non il logo orizzontale: su un documento ufficiale conta il contrassegno.
- La data è quella del giorno in cui il foglio viene costruito: un programma in discussione stampato tre mesi fa non deve sembrare quello di oggi.

## 25. Il calendario dell'agenda
- Il calendario si costruisce nel browser leggendo l'elenco degli incontri scritto nella pagina: il sito resta fatto di soli file, senza programmi che girano su un server. Senza JavaScript il calendario non compare e resta l'elenco, che basta da solo.
- Compare solo se c'è almeno un incontro. Un calendario di caselle vuote fa sembrare il sito abbandonato più di quanto farebbe la sua assenza.
- Il giorno con un incontro futuro è rosso, quello già svolto è grigio, oggi ha il bordo nero. Si clicca e si apre l'incontro.
- Sui telefoni stretti nella casella resta solo il giorno: il titolo sta nell'elenco sotto. Non si aggiungono mesi vuoti navigabili all'infinito senza motivo.

26. **Kit social.** Le immagini per i social si generano da `stampa/costruisci_social.py`,
    non si disegnano a mano: nascono dagli stessi titoli e slogan dei pilastri, così non
    possono dire una cosa diversa dal programma. Vanno rigenerate quando cambia un pilastro
    o quando arriva il dominio definitivo (finché l'indirizzo è più lungo di 34 caratteri
    resta fuori dall'immagine, perché troncato sarebbe illeggibile).

27. **PDF del programma.** `risorse/materiali/SA-programma-in-una-pagina.pdf` non si aggiorna
    da solo: dopo ogni modifica ai pilastri si rilancia `strumenti/programma_pdf.py`.

28. **Comuni.** `contenuti/comuni.json` tiene i 391 comuni siciliani con la loro provincia e
    si rigenera con `strumenti/scarica_comuni.py`. Serve a «Cosa succede vicino a me»: chi
    scrive il proprio paese non deve sapere a quale tavolo appartiene. Senza JavaScript
    restano le nove schede delle province: la funzione non è mai l'unica strada.

29. **Codice.** Il generatore è `costruisci.py` (quali pagine esistono) più il pacchetto
    `sito/` (i pezzi riusabili: testi, impaginazione, guscio). Dopo ogni modifica al codice
    che non deve cambiare l'aspetto del sito si lancia `strumenti/prova_uscita.py`: costruisce
    il sito prima e dopo e dice se è cambiato qualcosa che non doveva.

30. **Dipendenze.** Stanno in `requirements.txt`, bloccate a una versione precisa. Non si
    installa niente «all'ultima versione» nella pubblicazione: un aggiornamento di terzi non
    deve poter fermare il sito da solo.
