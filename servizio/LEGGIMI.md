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
