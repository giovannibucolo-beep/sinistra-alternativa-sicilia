// Prova del servizio adesioni: simula l'archivio D1 con lo SQLite di Node e ripercorre tutto il giro,
// dalla compilazione del modulo fino alla cancellazione. Si lancia con: node servizio/prova.mjs
import { DatabaseSync } from 'node:sqlite';
import servizio from './adesioni.js';

const db = new DatabaseSync(':memory:');
const DB = {
  prepare(q) {
    let args = [];
    const o = {
      bind(...a) { args = a; return o; },
      async run() { const s = db.prepare(q); const r = s.run(...args); return { meta: { changes: r.changes } }; },
      async first() { return db.prepare(q).get(...args) ?? null; },
      async all() { return { results: db.prepare(q).all(...args) }; },
    };
    return o;
  },
};
const poste = [];
globalThis.fetch = async (u, o) => { poste.push(JSON.parse(o.body)); return { ok: true }; };

const env = { DB, SITO_AMMESSO: 'https://esempio.org', SERVIZIO: 'https://adesioni.esempio.org',
              UTENTE: 'u', PAROLA: 'p', POSTA_CHIAVE: 'k', POSTA_DA: 'noi@esempio.org' };
const AUTH = { Authorization: 'Basic ' + Buffer.from('u:p').toString('base64') };

const invia = (corpo) => servizio.fetch(new Request('https://adesioni.esempio.org/', {
  method: 'POST', headers: { Origin: 'https://esempio.org', 'Content-Type': 'application/json' },
  body: JSON.stringify(corpo) }), env);
const apri = (p, h = {}) => servizio.fetch(new Request('https://adesioni.esempio.org' + p, { headers: h }), env);

let ok = 0, ko = 0;
const prova = (nome, cond) => { if (cond) { ok++; console.log('  ok  ' + nome); } else { ko++; console.log('  NO  ' + nome); } };

const base = { chi: 'persona', nome: 'Maria Rossi', email: 'Maria.Rossi@Esempio.IT', provincia: 'Catania',
               comune: 'Catania', tavolo: '02', consenso: true, notizie: true };

console.log('Giro completo di un’adesione');
let r = await invia(base);
prova('il modulo accetta l’adesione', r.status === 200);
let riga = db.prepare('SELECT * FROM adesioni').get();
prova('l’email è salvata in minuscolo', riga.email === 'maria.rossi@esempio.it');
prova('parte in attesa di conferma', riga.stato === 'in_attesa');
prova('ha un gettone', (riga.gettone || '').length === 48);
prova('ha chiesto le notizie', riga.notizie === 1);
prova('è partita l’email di conferma', poste.length === 1);
prova('l’email contiene il collegamento di conferma', poste[0].text.includes('/conferma?g=' + riga.gettone));
prova('l’email contiene il collegamento per cancellarsi', poste[0].text.includes('/cancellami?g=' + riga.gettone));

console.log('Prima della conferma non è nella lista');
let lista = await (await apri('/lista.txt', AUTH)).text();
prova('la lista è vuota', lista.trim() === '');

console.log('Doppia iscrizione');
await invia({ ...base, telefono: '333' });
prova('resta una riga sola', db.prepare('SELECT count(*) c FROM adesioni').get().c === 1);
riga = db.prepare('SELECT * FROM adesioni').get();
prova('il dato nuovo è aggiornato', riga.telefono === '333');

console.log('Conferma');
prova('un gettone sbagliato non conferma', (await apri('/conferma?g=xxx')).status === 200
      && !(await (await apri('/conferma?g=xxx')).text()).includes('confermata'));
let c = await apri('/conferma?g=' + riga.gettone);
prova('il gettone giusto conferma', (await c.text()).includes('Adesione confermata'));
riga = db.prepare('SELECT * FROM adesioni').get();
prova('lo stato è confermato', riga.stato === 'confermato');
prova('la data di conferma è salvata', !!riga.quando_confermato);
lista = await (await apri('/lista.txt', AUTH)).text();
prova('ora è nella lista', lista.trim() === 'maria.rossi@esempio.it');

console.log('Chi non vuole le notizie non entra nella lista');
await invia({ ...base, email: 'solo.tavolo@esempio.it', nome: 'Luca Verdi', notizie: false });
const g2 = db.prepare("SELECT gettone FROM adesioni WHERE email='solo.tavolo@esempio.it'").get().gettone;
await apri('/conferma?g=' + g2);
lista = await (await apri('/lista.txt', AUTH)).text();
prova('confermato ma fuori dalla lista notizie', !lista.includes('solo.tavolo'));
prova('è comunque fra le adesioni', db.prepare('SELECT count(*) c FROM adesioni').get().c === 2);

console.log('Cancellazione con un clic');
const g1 = db.prepare("SELECT gettone FROM adesioni WHERE email='maria.rossi@esempio.it'").get().gettone;
prova('la pagina conferma la cancellazione', (await (await apri('/cancellami?g=' + g1)).text()).includes('cancellati'));
riga = db.prepare('SELECT * FROM adesioni WHERE id = 1').get();
prova('lo stato è cancellato', riga.stato === 'cancellato');
prova('il nome è stato cancellato', riga.nome === '');
prova('l’email non c’è più', !riga.email.includes('maria'));
prova('il gettone non vale più', riga.gettone === null);
lista = await (await apri('/lista.txt', AUTH)).text();
prova('non è più nella lista', !lista.includes('maria'));

console.log('Difese');
prova('senza consenso non entra', (await invia({ ...base, email: 'x@y.it', consenso: false })).status === 400);
prova('email non valida respinta', (await invia({ ...base, email: 'non-una-email' })).status === 400);
prova('provincia inventata respinta', (await invia({ ...base, email: 'z@y.it', provincia: 'Milano' })).status === 400);
prova('la lista chiede la password', (await apri('/lista.txt')).status === 401);
prova('il pannello chiede la password', (await apri('/')).status === 401);
const trappola = await invia({ ...base, email: 'bot@y.it', sito_web: 'spam' });
prova('il campo trappola non salva niente', trappola.status === 200
      && !db.prepare("SELECT 1 FROM adesioni WHERE email='bot@y.it'").get());

console.log(`\n${ok} prove superate, ${ko} fallite`);
process.exit(ko ? 1 : 0);
