// Servizio che riceve le adesioni del sito e le tiene in un elenco riservato.
// Gira su Cloudflare Workers con un archivio D1 collegato con il nome DB. Nessun altro servizio vede i dati.
// Impostazioni (variabili del Worker): SITO_AMMESSO = indirizzo del sito, UTENTE e PAROLA = accesso all'elenco.
const CAMPI = ['chi', 'organizzazione', 'tipo_organizzazione', 'nome', 'email', 'telefono', 'comune', 'provincia', 'tavolo', 'mano'];
const PROVINCE = ['Agrigento', 'Caltanissetta', 'Catania', 'Enna', 'Messina', 'Palermo', 'Ragusa', 'Siracusa', 'Trapani'];
const TABELLA = `CREATE TABLE IF NOT EXISTS adesioni (id INTEGER PRIMARY KEY AUTOINCREMENT, quando TEXT NOT NULL, chi TEXT, organizzazione TEXT, tipo_organizzazione TEXT, nome TEXT NOT NULL, email TEXT NOT NULL, telefono TEXT, comune TEXT, provincia TEXT NOT NULL, tavolo TEXT, mano TEXT)`;

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
  if (d.consenso !== true) return risposta(env, 400, { errore: 'manca il consenso' });
  if (!r.nome || !/^[^@ ]+@[^@ ]+[.][^@ ]+$/.test(r.email) || !PROVINCE.includes(r.provincia)) return risposta(env, 400, { errore: 'dati incompleti' });
  if (r.chi === 'organizzazione' && !r.organizzazione) return risposta(env, 400, { errore: 'manca il nome dell’organizzazione' });
  await env.DB.prepare(TABELLA).run();
  await env.DB.prepare('INSERT INTO adesioni (quando, ' + CAMPI.join(', ') + ') VALUES (?, ' + CAMPI.map(() => '?').join(', ') + ')').bind(new Date().toISOString(), ...CAMPI.map(c => r[c])).run();
  return risposta(env, 200, { ok: true });
}

async function elenco(env) { await env.DB.prepare(TABELLA).run(); return (await env.DB.prepare('SELECT * FROM adesioni ORDER BY id DESC').all()).results || []; }

export default {
  async fetch(richiesta, env) {
    const u = new URL(richiesta.url);
    if (richiesta.method === 'OPTIONS') return new Response(null, { status: 204, headers: intestazioni(env) });
    if (richiesta.method === 'POST' && u.pathname === '/') return ricevi(richiesta, env);
    if (!autorizzato(richiesta, env)) return chiedi();
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
      const tab = righe.slice(0, 50).map(x => `<tr><td>${html(x.quando.slice(0, 10))}</td><td>${html(x.chi === 'organizzazione' ? x.organizzazione + ' (' + x.nome + ')' : x.nome)}</td><td>${html(x.email)}</td><td>${html(x.provincia)}</td><td>${html(x.tavolo || '')}</td></tr>`).join('');
      return new Response(`<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Adesioni</title><style>body{font:16px/1.5 system-ui;max-width:900px;margin:40px auto;padding:0 16px}td,th{padding:6px 10px;border-bottom:1px solid #ccc;text-align:left}a.b,button{display:inline-block;padding:12px 18px;background:#000;color:#fff;border:0;font:inherit;text-decoration:none;cursor:pointer}input{padding:11px;font:inherit}</style><h1>Adesioni: ${righe.length}</h1><p><a class="b" href="/elenco.csv">Scarica l’elenco completo (si apre con Excel o Numbers)</a></p><h2>Ultime 50</h2><table><tr><th>Data</th><th>Chi</th><th>Email</th><th>Provincia</th><th>Tavolo</th></tr>${tab}</table><h2>Cancellare una persona</h2><p>Quando qualcuno chiede di essere cancellato, scrivi qui la sua email.</p><form method="post" action="/cancella"><input type="email" name="email" required placeholder="email da cancellare"> <button>Cancella</button></form>`, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
    }
    return new Response('Non trovato', { status: 404 });
  },
};
