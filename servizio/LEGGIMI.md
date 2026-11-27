# Elenco riservato delle adesioni

`adesioni.js` è il piccolo servizio che riceve le adesioni dal sito e le tiene in un elenco che vede solo chi ha nome utente e parola d’ordine. Non passa da Google né da servizi di moduli.

Oggi **non è acceso**: serve un account Cloudflare intestato al coordinamento (gratuito per questi volumi).

## Che cosa fa
- Accetta adesioni solo dal nostro sito, solo con il consenso, solo con dati completi.
- Pagina riservata: quante adesioni ci sono, le ultime 50, pulsante «Scarica l’elenco» (si apre con Excel o Numbers).
- Cancellazione di una persona scrivendo la sua email (serve quando qualcuno lo chiede).

## Per accenderlo (tutto dal sito di Cloudflare, senza terminale)
1. Creare un archivio D1 (per esempio `adesioni`).
2. Creare un Worker e incollare il contenuto di `adesioni.js`.
3. Collegare l’archivio al Worker con il nome `DB`.
4. Impostare tre variabili: `SITO_AMMESSO` (indirizzo del sito), `UTENTE` e `PAROLA` (accesso all’elenco; la parola lunga e segreta).
5. Scrivere l’indirizzo del Worker in `contenuti/sito.json`, voce `modulo.invia_a`.
6. Scrivere in `legale.servizio_modulo` chi riceve i dati, così l’informativa privacy lo dichiara.

## Email di conferma (facoltativa)
Chi aderisce riceve una email che conferma l’adesione e dice come farsi cancellare. Parte solo se si impostano altre due variabili:
- `POSTA_CHIAVE`: la chiave del servizio di posta (Resend, gratuito fino a qualche migliaio di email al mese);
- `POSTA_DA`: l’indirizzo da cui parte la email (deve essere del nostro dominio e verificato dal servizio).

Senza queste due variabili non parte nessuna email e l’adesione viene registrata lo stesso. Se l’invio fallisce, l’adesione resta comunque salvata.

I nomi esatti dei menu di Cloudflare cambiano nel tempo: i passi 1–4 si fanno insieme al momento dell’apertura.

Il servizio è stato provato con 16 controlli (dati validi e non validi, accesso negato senza parola, cancellazione), ma non ancora su Cloudflare.


## La lista email: come si forma e come si aggiorna

La lista non si compila a mano: si forma da sé, e ogni riga ci arriva solo se la persona ha fatto due gesti distinti.

1. **Compila il modulo** sul sito e spunta «voglio ricevere gli aggiornamenti». La riga entra nell'archivio con lo stato **in attesa**: non è ancora in nessuna lista e non riceve niente.
2. **Riceve un'email** con un collegamento personale e lo apre. Solo allora lo stato diventa **confermato** e la riga entra nella lista.
3. **Si cancella quando vuole**, con il collegamento in fondo a ogni messaggio: un clic, nessuna password, nessuna email da scrivere. I dati vengono cancellati sul momento; resta solo la traccia che quella riga è stata cancellata.

Perché due passi e non uno: senza la conferma chiunque può iscrivere l'indirizzo di un altro, la lista si riempie di indirizzi sbagliati e dopo poche settimane i nostri messaggi finiscono nello spam di tutti. La conferma è ciò che tiene pulita la lista e difendibile il consenso.

### Due consensi distinti
Nel modulo ci sono due spunte separate: una per essere ricontattati dal coordinamento (obbligatoria) e una per ricevere le notizie (facoltativa). Chi dà solo la prima resta fra le adesioni e **non** entra nella lista degli invii.

### Nessun doppione
Chi si iscrive due volte non diventa due righe: la riga si aggiorna con i dati nuovi. Chi era già confermato resta confermato e non riceve una seconda email di conferma.

### Come si tira fuori la lista
Dal pannello riservato, in alto, tre pulsanti:
- **Scarica tutto** — tutte le adesioni con tutti i campi, per lavorarci con Excel o Numbers.
- **Lista notizie (CSV)** — solo chi è confermato e ha chiesto le notizie: email, nome, provincia. È il file da dare al programma che invia.
- **Lista notizie (solo indirizzi)** — un indirizzo per riga, da incollare dove serve.

Il pannello mostra sempre quattro numeri: confermate, in attesa di conferma, nella lista notizie, cancellate.

### Che cosa serve perché tutto questo si accenda
- L'indirizzo pubblico del servizio nella variabile `SERVIZIO` (serve a costruire i collegamenti di conferma e cancellazione: senza, l'email di conferma non li contiene).
- `POSTA_CHIAVE` e `POSTA_DA` per l'invio dell'email di conferma.
- Un dominio vostro con la posta firmata, altrimenti le email di conferma finiscono nello spam e la lista non cresce.

### Prova
`node servizio/prova.mjs` ripercorre tutto il giro — iscrizione, doppione, conferma, cancellazione, difese — su un archivio finto. Trenta controlli. Va rilanciata dopo ogni modifica al servizio.
