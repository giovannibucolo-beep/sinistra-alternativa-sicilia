#!/usr/bin/env python3
"""Esame di accessibilità su ogni pagina del sito, misurato nel browser.

Controlla le cose che si possono misurare davvero: contrasto del testo (WCAG 2.1 AA:
4.5 per il testo normale, 3 per quello grande), immagini senza descrizione, comandi
senza nome, campi senza etichetta, ordine dei titoli, landmark, lingua della pagina,
identificativi ripetuti, collegamenti che aprono una finestra nuova senza protezione.

Serve il sito già costruito. Si lancia con: python3 strumenti/prova_accesso.py
"""
import functools, http.server, json, pathlib, threading, sys

RADICE = pathlib.Path(__file__).resolve().parent.parent
OUT = RADICE / 'pubblico'
PORTA = 8934

ESAME = r"""
() => {
  const out = [];
  const vis = el => { const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null; };
  const nascosto = el => el.closest('[aria-hidden="true"]') !== null;
  const nome = el => (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '').trim()
      || (el.querySelector('img[alt]') ? el.querySelector('img[alt]').alt.trim() : '');

  document.querySelectorAll('img').forEach(i => {
    if (!i.hasAttribute('alt')) out.push('immagine senza descrizione: ' + i.getAttribute('src')); });
  document.querySelectorAll('a[href], button').forEach(a => {
    if (vis(a) && !nascosto(a) && !nome(a)) out.push('comando senza nome: <' + a.tagName.toLowerCase() + '> ' + (a.getAttribute('href') || '')); });
  document.querySelectorAll('input, select, textarea').forEach(c => {
    if (c.type === 'hidden' || nascosto(c)) return;
    const lab = c.id && document.querySelector('label[for="' + CSS.escape(c.id) + '"]');
    if (!lab && !c.getAttribute('aria-label') && !c.closest('label')) out.push('campo senza etichetta: ' + (c.name || c.type)); });
  const conta = {};
  document.querySelectorAll('[id]').forEach(el => { conta[el.id] = (conta[el.id] || 0) + 1; });
  Object.entries(conta).filter(([, n]) => n > 1).forEach(([k, n]) => out.push('identificativo ripetuto ' + n + ' volte: #' + k));
  document.querySelectorAll('[tabindex]').forEach(el => {
    if (+el.getAttribute('tabindex') > 0) out.push('tabindex positivo: scompagina l’ordine di navigazione'); });
  document.querySelectorAll('a[target="_blank"]').forEach(a => {
    if (!(a.rel || '').includes('noopener')) out.push('finestra nuova senza noopener: ' + a.href); });
  if (!document.documentElement.lang) out.push('manca la lingua della pagina');
  if (!document.querySelector('main')) out.push('manca il contenuto principale <main>');
  const liv = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(vis).map(x => +x.tagName[1]);
  const uno = liv.filter(x => x === 1).length;
  if (uno !== 1) out.push('titoli di primo livello: ' + uno + ' (ne serve uno)');
  for (let i = 1; i < liv.length; i++)
    if (liv[i] - liv[i - 1] > 1) out.push('salto nei livelli dei titoli: h' + liv[i - 1] + ' → h' + liv[i]);

  const lum = c => { const [r, g, b] = c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number)
      .map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const fondo = el => { let n = el;
    while (n && n !== document.documentElement) { const c = getComputedStyle(n).backgroundColor;
      if (c && !c.includes('rgba(0, 0, 0, 0)')) return c; n = n.parentElement; }
    return 'rgb(255, 255, 255)'; };
  const visti = new Set();
  document.querySelectorAll('p,span,a,li,h1,h2,h3,h4,h5,h6,small,strong,em,b,button,label,td,th,figcaption,dt,dd').forEach(el => {
    if (!vis(el) || nascosto(el) || !el.textContent.trim() || el.children.length) return;
    const s = getComputedStyle(el), f = s.color, b = fondo(el);
    const r = (Math.max(lum(f), lum(b)) + 0.05) / (Math.min(lum(f), lum(b)) + 0.05);
    const px = parseFloat(s.fontSize);
    const soglia = (px >= 24 || (px >= 18.66 && +s.fontWeight >= 700)) ? 3 : 4.5;
    if (r < soglia) { const k = f + '|' + b + '|' + soglia;
      if (!visti.has(k)) { visti.add(k);
        out.push('contrasto ' + r.toFixed(2) + ', ne serve ' + soglia + ': ' + f + ' su ' + b
                 + ' — «' + el.textContent.trim().slice(0, 40) + '»'); } } });
  return out;
}
"""

if not OUT.exists():
    raise SystemExit('Prima costruisci il sito: python3 costruisci.py')
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit('Serve Playwright: pip install playwright --break-system-packages && playwright install chromium')

# admin/ è il pannello di scrittura, una pagina di terzi: non è roba che scriviamo noi
pagine = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*.html')
                if not p.relative_to(OUT).as_posix().startswith('admin/'))
gestore = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
server = http.server.ThreadingHTTPServer(('127.0.0.1', PORTA), gestore)
threading.Thread(target=server.serve_forever, daemon=True).start()

problemi = {}
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 900})
        for p in pagine:
            pg.goto(f'http://127.0.0.1:{PORTA}/{p}')
            pg.wait_for_timeout(250)
            trovati = pg.evaluate(ESAME)
            if trovati:
                problemi[p] = trovati
        b.close()
finally:
    server.shutdown()

for p, elenco in problemi.items():
    for x in elenco:
        print(f'{p}: {x}')
print(f'\npagine esaminate: {len(pagine)} · pagine con problemi: {len(problemi)} · '
      f'problemi: {sum(len(v) for v in problemi.values())}')
sys.exit(1 if problemi else 0)
