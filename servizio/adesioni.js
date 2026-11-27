// Servizio che riceve le adesioni del sito e le tiene in un elenco riservato.
// Gira su Cloudflare Workers con un archivio D1 collegato con il nome DB. Nessun altro servizio vede i dati.
// Impostazioni (variabili del Worker): SITO_AMMESSO = indirizzo del sito, UTENTE e PAROLA = accesso all'elenco.
const CAMPI = ['chi', 'organizzazione', 'tipo_organizzazione', 'nome', 'email', 'telefono', 'comune', 'provincia', 'tavolo', 'mano'];
// Stati di una riga: in_attesa (ha compilato, non ha ancora cliccato la conferma), confermato, cancellato.
// Nella lista per gli invii entrano solo i «confermato» che hanno detto sì alle notizie.
const PROVINCE = ['Agrigento', 'Caltanissetta', 'Catania', 'Enna', 'Messina', 'Palermo', 'Ragusa', 'Siracusa', 'Trapani'];
const TABELLA = `CREATE TABLE IF NOT EXISTS adesioni (id INTEGER PRIMARY KEY AUTOINCREMENT, quando TEXT NOT NULL, chi TEXT, organizzazione TEXT, tipo_organizzazione TEXT, nome TEXT NOT NULL, email TEXT NOT NULL, telefono TEXT, comune TEXT, provincia TEXT NOT NULL, tavolo TEXT, mano TEXT)`;
const AGGIUNTE = [
  "ALTER TABLE adesioni ADD COLUMN stato TEXT NOT NULL DEFAULT 'in_attesa'",
  'ALTER TABLE adesioni ADD COLUMN gettone TEXT',
  'ALTER TABLE adesioni ADD COLUMN notizie INTEGER NOT NULL DEFAULT 0',
  'ALTER TABLE adesioni ADD COLUMN quando_confermato TEXT',
  'ALTER TABLE adesioni ADD COLUMN quando_cancellato TEXT',
];
const INDICE = 'CREATE UNIQUE INDEX IF NOT EXISTS adesioni_email ON adesioni (email)';
let preparato = false;

// Prepara la tabella una volta per avvio. Le colonne aggiunte dopo: se ci sono già, l'errore si ignora.
async function prepara(env) {
  if (preparato) return;
  await env.DB.prepare(TABELLA).run();
  for (const q of AGGIUNTE) { try { await env.DB.prepare(q).run(); } catch (e) { /* colonna già presente */ } }
  try { await env.DB.prepare(INDICE).run(); } catch (e) { /* doppioni storici: l'indice si crea a mano */ }
  preparato = true;
}

// Gettone non indovinabile: serve per confermare e per cancellarsi senza password.
function gettone() {
  const b = new Uint8Array(24);
  crypto.getRandomValues(b);
  return Array.from(b, x => x.toString(16).padStart(2, '0')).join('');
}

const pulisci = (v, max = 200) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);
const csv = v => { let s = String(v == null ? '' : v); if (/^[=+\-@]/.test(s)) s = "'" + s; return '"' + s.replace(/"/g, '""') + '"'; };
const html = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function origine(env) { try { return new URL(env.SITO_AMMESSO).origin; } catch (e) { return ''; } }
function intestazioni(env) { return { 'Access-Control-Allow-Origin': origine(env), 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept', 'Vary': 'Origin' }; }
function risposta(env, stato, corpo) { return new Response(JSON.stringify(corpo), { status: stato, headers: { 'Content-Type': 'application/json; charset=utf-8', ...intestazioni(env) } }); }

function autorizzato(richiesta, env) {
  if (!env.UTENTE || !env.PAROLA) return false;
  const a = richiesta.headers.get('Authorization') || '';
  if (!a.startsWith('Basic ')) return false;
  let chiaro = ''; try { chiaro = atob(a.slice(6)); } catch (e) { return false; }
  const atteso = env.UTENTE + ':' + env.PAROLA;
  if (chiaro.length !== atteso.length) return false;
  let diff = 0; for (let i = 0; i < atteso.length; i++) diff |= chiaro.charCodeAt(i) ^ atteso.charCodeAt(i);
  return diff === 0;
}
const chiedi = () => new Response('Accesso riservato', { status: 401, headers: { 'WWW-Authenticate': 'Basic realm="Adesioni", charset="UTF-8"' } });

async function ricevi(richiesta, env) {
  if (!origine(env) || richiesta.headers.get('Origin') !== origine(env)) return risposta(env, 403, { errore: 'origine non ammessa' });
  let d; try { d = JSON.parse((await richiesta.text()).slice(0, 5000)); } catch (e) { return risposta(env, 400, { errore: 'dati non leggibili' }); }
  if (d.sito_web) return risposta(env, 200, { ok: true });
  const r = { chi: d.chi === 'organizzazione' ? 'organizzazione' : 'persona', organizzazione: pulisci(d.organizzazione), tipo_organizzazione: pulisci(d.tipo_organizzazione, 40), nome: pulisci(d.nome), email: pulisci(d.email).toLowerCase(), telefono: pulisci(d.telefono, 30), comune: pulisci(d.comune, 80), provincia: pulisci(d.provincia, 20), tavolo: pulisci(d.tavolo, 2), mano: pulisci(Array.isArray(d.mano) ? d.mano.join('; ') : d.mano, 300) };
  r.notizie = d.notizie === true ? 1 : 0;
  if (d.consenso !== true) return risposta(env, 400, { errore: 'manca il consenso' });
  if (!r.nome || !/^[^@ ]+@[^@ ]+[.][^@ ]+$/.test(r.email) || !PROVINCE.includes(r.provincia)) return risposta(env, 400, { errore: 'dati incompleti' });
  if (r.chi === 'organizzazione' && !r.organizzazione) return risposta(env, 400, { errore: 'manca il nome dell’organizzazione' });
  await prepara(env);
  // Chi si iscrive due volte non diventa due righe: la riga si aggiorna e il gettone si rinnova.
  const g = gettone();
  const esiste = await env.DB.prepare('SELECT id, stato FROM adesioni WHERE email = ?').bind(r.email).first();
  if (esiste) {
    await env.DB.prepare('UPDATE adesioni SET quando = ?, ' + CAMPI.map(c => c + ' = ?').join(', ')
      + ", notizie = ?, gettone = ?, quando_cancellato = NULL, stato = CASE WHEN stato = 'confermato' THEN 'confermato' ELSE 'in_attesa' END WHERE id = ?")
      .bind(new Date().toISOString(), ...CAMPI.map(c => r[c]), r.notizie, g, esiste.id).run();
  } else {
    await env.DB.prepare('INSERT INTO adesioni (quando, ' + CAMPI.join(', ') + ', notizie, gettone, stato) VALUES (?, '
      + CAMPI.map(() => '?').join(', ') + ", ?, ?, 'in_attesa')")
      .bind(new Date().toISOString(), ...CAMPI.map(c => r[c]), r.notizie, g).run();
  }
  await conferma(env, r, g, esiste && esiste.stato === 'confermato');
  return risposta(env, 200, { ok: true });
}

// Email di conferma a chi aderisce. Parte solo se sono impostate POSTA_CHIAVE e POSTA_DA (servizio Resend).
// Se non sono impostate, o se l'invio fallisce, l'adesione resta comunque registrata.
async function conferma(env, r, g, gia) {
  if (!env.POSTA_CHIAVE || !env.POSTA_DA) return;
  const base = (env.SERVIZIO || '').replace(/\/$/, '');
  const nome = r.chi === 'organizzazione' ? r.organizzazione : r.nome.split(' ')[0];
  const righe = [
    'Ciao ' + nome + ',',
    '',
    'abbiamo ricevuto la tua adesione per la provincia di ' + r.provincia + '.',
  ];
  if (!gia && base) {
    righe.push('', 'Manca un passaggio solo: apri questo collegamento e la tua adesione è valida.',
               '', base + '/conferma?g=' + g,
               '', 'Finché non lo apri non ti scriviamo e non entri in nessuna lista.');
  } else {
    righe.push('', 'Ti scriveremo quando ci sarà un incontro nel tuo territorio.');
  }
  if (r.mano) righe.push('', 'Hai dato la tua disponibilità per: ' + r.mano + '. Ti ricontattiamo noi.');
  if (base) righe.push('', 'Se non sei stato tu, ignora questo messaggio. Per cancellarti in qualsiasi momento: ' + base + '/cancellami?g=' + g);
  else righe.push('', 'Se non sei stato tu, o se vuoi essere cancellato, rispondi a questa email: cancelliamo subito i tuoi dati.');
  if (env.SITO_AMMESSO) righe.push('', env.SITO_AMMESSO);
  try {
    await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + env.POSTA_CHIAVE, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: env.POSTA_DA, to: [r.email], subject: 'Abbiamo ricevuto la tua adesione', text: righe.join('\n') }),
    });
  } catch (e) { /* l'adesione è già salvata: un errore di posta non la annulla */ }
}

async function elenco(env) { await prepara(env); return (await env.DB.prepare('SELECT * FROM adesioni ORDER BY id DESC').all()).results || []; }

// La lista vera per gli invii: solo chi ha confermato e ha chiesto le notizie.
async function lista(env) {
  await prepara(env);
  return (await env.DB.prepare("SELECT nome, email, provincia FROM adesioni WHERE stato = 'confermato' AND notizie = 1 ORDER BY email").all()).results || [];
}

function pagina_semplice(titolo, testo) {
  return new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${html(titolo)}</title><style>body{font:17px/1.6 system-ui,sans-serif;max-width:34em;margin:12vh auto;padding:0 20px}h1{font-size:28px;line-height:1.15}</style><h1>${html(titolo)}</h1><p>${html(testo)}</p>`,
    { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
}

export default {
  async fetch(richiesta, env) {
    const u = new URL(richiesta.url);
    if (richiesta.method === 'OPTIONS') return new Response(null, { status: 204, headers: intestazioni(env) });
    if (richiesta.method === 'POST' && u.pathname === '/') return ricevi(richiesta, env);

    // Due indirizzi aperti a tutti, protetti dal gettone e non dalla password:
    // uno conferma l'adesione, l'altro cancella. Senza gettone valido non fanno niente.
    if (richiesta.method === 'GET' && u.pathname === '/conferma') {
      await prepara(env);
      const g = pulisci(u.searchParams.get('g'), 64);
      const f = g && await env.DB.prepare("SELECT id, nome FROM adesioni WHERE gettone = ? AND stato <> 'cancellato'").bind(g).first();
      if (!f) return pagina_semplice('Collegamento non valido', 'Questo collegamento è scaduto o già usato. Se vuoi, compila di nuovo il modulo di adesione sul sito.');
      await env.DB.prepare("UPDATE adesioni SET stato = 'confermato', quando_confermato = ? WHERE id = ?").bind(new Date().toISOString(), f.id).run();
      return pagina_semplice('Adesione confermata', 'Grazie. Ti scriviamo noi quando c’è un incontro nel tuo territorio.');
    }
    if (richiesta.method === 'GET' && u.pathname === '/cancellami') {
      await prepara(env);
      const g = pulisci(u.searchParams.get('g'), 64);
      const f = g && await env.DB.prepare('SELECT id FROM adesioni WHERE gettone = ?').bind(g).first();
      if (!f) return pagina_semplice('Collegamento non valido', 'Questo collegamento non corrisponde a nessuna adesione.');
      // Si cancellano i dati, non si tiene una riga con dentro la persona: resta solo la traccia che è stata cancellata.
      await env.DB.prepare("UPDATE adesioni SET stato = 'cancellato', quando_cancellato = ?, gettone = NULL, notizie = 0, nome = '', email = 'cancellato-' || id, telefono = '', comune = '', organizzazione = '', mano = '' WHERE id = ?").bind(new Date().toISOString(), f.id).run();
      return pagina_semplice('Cancellazione fatta', 'I tuoi dati sono stati cancellati. Non riceverai più nostri messaggi.');
    }

    if (!autorizzato(richiesta, env)) return chiedi();
    if (richiesta.method === 'GET' && u.pathname === '/lista.txt') {
      const r = await lista(env);
      return new Response(r.map(x => x.email).join('\n') + (r.length ? '\n' : ''),
        { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Content-Disposition': 'attachment; filename="lista.txt"', 'Cache-Control': 'no-store' } });
    }
    if (richiesta.method === 'GET' && u.pathname === '/lista.csv') {
      const r = await lista(env), col = ['email', 'nome', 'provincia'];
      return new Response('\ufeff' + [col.map(csv).join(';'), ...r.map(x => col.map(c => csv(x[c])).join(';'))].join('\r\n'),
        { headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'attachment; filename="lista-notizie.csv"', 'Cache-Control': 'no-store' } });
    }
    if (richiesta.method === 'GET' && u.pathname === '/elenco.csv') {
      const righe = await elenco(env), col = ['id', 'quando', ...CAMPI];
      return new Response('﻿' + [col.map(csv).join(';'), ...righe.map(x => col.map(c => csv(x[c])).join(';'))].join('\r\n'), { headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'attachment; filename="adesioni.csv"', 'Cache-Control': 'no-store' } });
    }
    if (richiesta.method === 'POST' && u.pathname === '/cancella') {
      const email = pulisci((await richiesta.formData()).get('email')).toLowerCase();
      const fatto = await env.DB.prepare('DELETE FROM adesioni WHERE email = ?').bind(email).run();
      return new Response(`<!doctype html><meta charset="utf-8"><title>Adesioni</title><p>Cancellate ${(fatto.meta && fatto.meta.changes) || 0} adesioni di ${html(email)}.</p><p><a href="/">Torna all’elenco</a></p>`, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
    }
    if (richiesta.method === 'GET' && u.pathname === '/') {
      const righe = await elenco(env);
      const tab = righe.slice(0, 50).map(x => `<tr><td>${html(x.quando.slice(0, 10))}</td><td>${html(x.chi === 'organizzazione' ? x.organizzazione + ' (' + x.nome + ')' : x.nome)}</td><td>${html(x.email)}</td><td>${html(x.provincia)}</td><td>${html(x.stato === 'confermato' ? (x.notizie ? 'confermato · notizie' : 'confermato') : x.stato || 'in attesa')}</td></tr>`).join('');
      return new Response(`<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Adesioni</title><style>body{font:16px/1.5 system-ui;max-width:900px;margin:40px auto;padding:0 16px}td,th{padding:6px 10px;border-bottom:1px solid #ccc;text-align:left}a.b,button{display:inline-block;padding:12px 18px;background:#000;color:#fff;border:0;font:inherit;text-decoration:none;cursor:pointer}input{padding:11px;font:inherit}</style><h1>Adesioni: ${righe.filter(x => x.stato !== 'cancellato').length}</h1><p>Confermate: <b>${righe.filter(x => x.stato === 'confermato').length}</b> · In attesa di conferma: <b>${righe.filter(x => x.stato === 'in_attesa').length}</b> · Nella lista per le notizie: <b>${righe.filter(x => x.stato === 'confermato' && x.notizie).length}</b> · Cancellate: ${righe.filter(x => x.stato === 'cancellato').length}</p><p><a class="b" href="/elenco.csv">Scarica tutto</a> <a class="b" href="/lista.csv">Lista notizie (CSV)</a> <a class="b" href="/lista.txt">Lista notizie (solo indirizzi)</a></p><h2>Ultime 50</h2><table><tr><th>Data</th><th>Chi</th><th>Email</th><th>Provincia</th><th>Stato</th></tr>${tab}</table><h2>Cancellare una persona</h2><p>Quando qualcuno chiede di essere cancellato, scrivi qui la sua email.</p><form method="post" action="/cancella"><input type="email" name="email" required placeholder="email da cancellare"> <button>Cancella</button></form>`, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
    }
    return new Response('Non trovato', { status: 404 });
  },
};
