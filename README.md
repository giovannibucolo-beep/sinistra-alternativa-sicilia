# Sito di Sinistra per l'Alternativa — Sicilia

Il sito è fatto di **testi** (cartella `contenuti/`) e di **grafica** (cartella `risorse/`).
Chi aggiorna il sito tocca solo i testi. Le pagine si costruiscono e si pubblicano da sole.

## Aggiungere una notizia (dal browser, senza installare niente)

1. Su GitHub apri la cartella `contenuti/notizie/`.
2. **Add file → Create new file**.
3. Nome del file: data e poche parole, senza spazi né accenti. Esempio: `2026-12-03-assemblea-a-enna.md`
4. Incolla e modifica:

```
---
titolo: Enna, assemblea sugli ospedali delle aree interne
data: 2026-12-03
luogo: Enna
sintesi: Una riga che riassume la notizia: compare negli elenchi e nelle anteprime.
---

Primo capoverso della notizia.

Secondo capoverso. Una riga vuota separa i capoversi.

## Un titoletto

- un punto elenco
- un altro punto

**Grassetto** fra doppi asterischi. Un collegamento: [testo](https://indirizzo.it)
```

5. **Commit changes**. Dopo un paio di minuti la notizia è in linea.

Per la foto: carica in `risorse/img/` un file `.jpg` con **lo stesso nome** della notizia
(`2026-12-03-assemblea-a-enna.jpg`). Finché manca, la pagina mostra un segnaposto.

## Aggiungere un incontro

Stessa cosa nella cartella `contenuti/agenda/`:

```
---
titolo: Enna: tavolo sanità
data: 2026-12-17
ora: 18:00
luogo: Enna · Sala comunale
provincia: Enna
pilastro: 03
---

Due righe su che cosa si fa e chi può partecipare.
```

`provincia` lo fa comparire nella pagina della provincia; `pilastro` (da 01 a 07) nella pagina del pilastro.
Le stesse due righe funzionano anche nelle notizie: la notizia compare nella pagina del pilastro e in quella della provincia.
L'incontro passa da solo fra quelli «già svolti» il giorno dopo.

## Le altre cartelle

| Cartella | Che cosa contiene |
|---|---|
| `contenuti/pilastri/` | I sette pilastri del programma |
| `contenuti/territori/` | Una pagina per provincia: lotte, referente, contatto |
| `contenuti/pagine/` | Chi siamo, privacy, note legali |
| `contenuti/sito.json` | Nome, contatti, versione, indirizzo del servizio per le adesioni |

Una riga `esempio: sì` nell'intestazione mette l'etichetta «esempio» sulla pagina: va tolta quando il contenuto è vero.

## Bozze: scrivere senza pubblicare

Una riga `bozza: sì` nell'intestazione di una notizia o di un incontro lo tiene **fuori dal sito pubblico**.
Il file resta nella cartella, pronto: quando il testo è verificato e approvato si toglie la riga e va in linea.

## Come è scritto un pilastro

Due capitoli fissi, che diventano i due riquadri della pagina:

```
## Cosa può fare la Regione, subito

- una proposta per riga

## Cosa va strappato allo Stato

- una legge-voto per riga
```

Quello che segue (altri `## titoli`) compare sotto come testo normale.

## Che cosa succede quando salvi

1. Il sito viene ricostruito (`costruisci.py`).
2. Viene controllato (`controlla.py`): collegamenti rotti, titoli mancanti, anteprime.
3. Se un controllo fallisce **non viene pubblicato nulla** e il sito in linea resta quello di prima.
   L'errore si legge nella scheda **Actions** del repository.

## Prima di aprire il sito al pubblico

In `contenuti/sito.json`:
- `modulo.invia_a`: indirizzo del servizio che riceve le adesioni (oggi vuoto: il modulo non invia nulla);
- `contatti`: quelli veri, poi `"reali": true`;
- `bozza`: `false` toglie l'etichetta «bozza dimostrativa»;
- `indicizzabile`: `true` fa comparire il sito nei motori di ricerca;
- `versione`: 1.0 è la prima approvata dal coordinamento.

Vanno scritte le pagine `privacy` e `note-legali`.

## Per chi lavora al codice

- `python3 costruisci.py` costruisce il sito in `pubblico/` (solo libreria standard).
- `python3 controlla.py` lo controlla.
- `strumenti/anteprime.py` ridisegna le immagini di anteprima per i social; `strumenti/prova_resa.py` apre ogni pagina a misura telefono e computer. Servono Playwright e Chrome.
