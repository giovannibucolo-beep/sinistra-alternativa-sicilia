# Pannello di scrittura

Si apre su `…/admin/` del sito. Da lì si scrivono notizie, incontri, pagine delle province e impostazioni, e si pubblica: ogni salvataggio scrive un file nel repository, i controlli partono da soli e il sito si ricostruisce.

Il pannello è **Sveltia CMS**: non è un programma che gira da qualche parte, è una pagina che si carica nel browser di chi scrive. Non c'è niente da aggiornare e niente da pagare.

## Entrare la prima volta (per Giovanni, 5 minuti)

Il modo più rapido non richiede di registrare nessuna applicazione: si entra con una chiave personale di GitHub.

1. Su GitHub: **Settings › Developer settings › Personal access tokens**, crea una chiave nuova.
2. Permessi: per una chiave «fine-grained» servono **Contents** e **Pull requests** in lettura e scrittura, solo su questo repository. Per una chiave classica serve l'ambito **repo**.
3. Copia la chiave (si vede una volta sola).
4. Apri `…/admin/` sul sito e scegli **Sign In with Token**, poi incolla la chiave.

La chiave resta nel browser di chi entra: non va messa in nessun file e non va mandata a nessuno.

## Far entrare altre persone (dopo)

Perché anche redtano o un referente provinciale possano entrare senza maneggiare chiavi, serve un piccolo servizio di accesso, da mettere sullo stesso account Cloudflare delle adesioni: si chiama **Sveltia CMS Authenticator** e si installa registrando una GitHub App. Poi nel `config.yml`, sotto `backend`, si aggiunge `base_url` con l'indirizzo di quel servizio.

Chi entra deve comunque essere collaboratore del repository: senza, può leggere ma non salvare.

## Come si lavora in due

Il pannello è configurato con il percorso **bozza → in revisione → pubblicato**. Chi scrive manda in revisione; chi ha il permesso di pubblicare approva. Dietro le quinte sono rami e richieste di modifica di GitHub, ma non serve saperlo.

## Fotografie

Autore e licenza non sono facoltativi: sono due campi del modulo e senza di essi la foto non compare in pagina. La foto va messa in `risorse/img` con lo stesso nome del file della notizia, e viene ottimizzata da sola alla pubblicazione.

## Se qualcosa non torna

Il pannello non può rompere il sito: se un controllo fallisce, la pubblicazione si ferma e il sito resta quello di prima. L'errore compare nella scheda **Actions** del repository.
