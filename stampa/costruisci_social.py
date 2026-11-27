#!/usr/bin/env python3
"""Costruisce il kit social: un'immagine quadrata e una verticale per ciascun pilastro,
più la coppia per l'adesione. Stessi contenuti del sito, stessa identità della carta.

Scrive i PNG in `risorse/materiali/social/` e li raccoglie in `SA-social-kit.zip`
insieme ai testi già scritti, così chi fa propaganda scarica un file e pubblica.

Si lancia con: python3 stampa/costruisci_social.py
"""
import json, pathlib, re, threading, http.server, functools, zipfile

QUI = pathlib.Path(__file__).resolve().parent
RADICE = QUI.parent
SITO = json.loads((RADICE / 'contenuti' / 'sito.json').read_text(encoding='utf-8'))
INDIRIZZO = SITO['indirizzo'].replace('https://', '').rstrip('/')
# Un indirizzo lungo su un'immagine si tronca e diventa illeggibile: finché il dominio
# definitivo non c'è, l'immagine porta solo la campagna. Le immagini vanno rigenerate
# quando il dominio cambia.
MOSTRA_INDIRIZZO = len(INDIRIZZO) <= 34
if not MOSTRA_INDIRIZZO:
    print(f'Indirizzo troppo lungo per le immagini ({INDIRIZZO}): resta fuori finché non c\'è il dominio definitivo.')
USCITA = RADICE / 'risorse' / 'materiali' / 'social'
USCITA.mkdir(parents=True, exist_ok=True)

P = []
for f in sorted((RADICE / 'contenuti' / 'pilastri').glob('*.md')):
    d = dict(re.findall(r'^([a-z_]+): (.*)$', f.read_text(encoding='utf-8').split('---')[1], re.M))
    d = {k: v.strip().strip('"') for k, v in d.items()}
    P.append(d)
P.sort(key=lambda x: x['numero'])

SITO_RIGA = f'<span class="sito">{INDIRIZZO}</span>' if MOSTRA_INDIRIZZO else '<span class="sito">Aderisci sul sito</span>'
SITO_RIGA_ADERISCI = f'<span class="sito">{INDIRIZZO}/aderisci.html</span>' if MOSTRA_INDIRIZZO else '<span class="sito">Aderisci sul sito</span>'

MISURE = {'quadrato': (1080, 1080), 'storia': (1080, 1920)}

STILE = '''
@font-face { font-family: Montserrat; font-weight: 500; src: url(../risorse/font/montserrat-latin-500-normal.woff2) format("woff2"); }
@font-face { font-family: Montserrat; font-weight: 800; src: url(../risorse/font/montserrat-latin-800-normal.woff2) format("woff2"); }
@font-face { font-family: Montserrat; font-weight: 900; src: url(../risorse/font/montserrat-latin-900-normal.woff2) format("woff2"); }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Montserrat, sans-serif; background: #000; color: #fff; }
.tela { position: relative; display: flex; flex-direction: column; justify-content: space-between;
        padding: 72px 72px 64px; overflow: hidden; background: #000; }
.tela::after { content: ""; position: absolute; inset: 28px; border: 2px solid rgba(255,255,255,.14); pointer-events: none; }
.alto { display: flex; align-items: flex-start; justify-content: space-between; gap: 32px; }
.num { font-weight: 900; font-size: 190px; line-height: .78; color: #EC3657; letter-spacing: -.04em; }
.mono { width: 118px; height: auto; }
.centro { margin-top: auto; padding: 0 0 56px; }
h1 { font-weight: 900; font-size: 92px; line-height: .98; letter-spacing: -.02em; text-wrap: balance; }
.slogan { margin-top: 34px; font-weight: 800; font-size: 44px; line-height: 1.16; color: #fff; text-wrap: balance; }
.riga { width: 160px; height: 8px; margin-top: 40px; background: #EC3657; }
.basso { display: flex; align-items: flex-end; justify-content: space-between; gap: 28px; }
.campagna { font-weight: 800; font-size: 28px; line-height: 1.24; letter-spacing: .1em; text-transform: uppercase; color: rgba(255,255,255,.72); white-space: nowrap; }
.sito { font-weight: 900; font-size: 30px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 620px; text-align: right; }
.storia .num { font-size: 260px; }
.storia h1 { font-size: 118px; }
.storia .slogan { font-size: 52px; margin-top: 46px; }
.storia .sito { font-size: 34px; max-width: 640px; }
.storia .mono { width: 150px; }
.aderisci h1 { font-size: 104px; }
.aderisci .contr { width: 300px; height: 300px; }
.storia.aderisci .contr { width: 420px; height: 420px; }
'''


def tela(forma, dentro, extra=''):
    w, h = MISURE[forma]
    return (f'<!DOCTYPE html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n<title>social</title>\n'
            f'<style>{STILE}.tela {{ width: {w}px; height: {h}px; }}</style>\n</head>\n<body>\n'
            f'<div class="tela {forma} {extra}">{dentro}</div>\n</body>\n</html>\n')


def pilastro(p, forma):
    return tela(forma, f'''
  <div class="alto"><span class="num">{p["numero"]}</span>
    <img class="mono" src="../risorse/loghi/sa-monogramma-bianco.svg" alt="SA"></div>
  <div class="centro">
    <h1>{p["titolo"]}</h1>
    <p class="slogan">{p["slogan"]}</p>
    <div class="riga"></div>
  </div>
  <div class="basso"><span class="campagna">La Sicilia<br>che SA</span>{SITO_RIGA}</div>''')


def adesione(forma):
    return tela(forma, f'''
  <div class="alto"><img class="contr" src="../risorse/loghi/sa-contrassegno-negativo-su-nero.svg" alt="">
    <img class="mono" src="../risorse/loghi/sa-monogramma-bianco.svg" alt="SA"></div>
  <div class="centro">
    <h1>Un programma nato dalle lotte.</h1>
    <p class="slogan">Fuori dal centrodestra, fuori dal «campo largo». Aderisci: ti scriviamo per gli incontri nella tua provincia.</p>
    <div class="riga"></div>
  </div>
  <div class="basso"><span class="campagna">La Sicilia<br>che SA</span>{SITO_RIGA_ADERISCI}</div>''', 'aderisci')


TESTI = ['KIT SOCIAL — SINISTRA PER L\'ALTERNATIVA',
         'Testi già scritti. Copiali, pubblicali con l\'immagine che porta lo stesso numero.',
         'Regola sola: non aggiungere promesse che il programma non fa.', '']
for p in P:
    TESTI += [f'--- PILASTRO {p["numero"]} · {p["titolo"]} ---',
              f'{p["titolo"].upper()}. {p["slogan"]}', '',
              p['sintesi'], '',
              f'Il punto per intero: {SITO["indirizzo"].rstrip("/")}/programma/{p["numero"]}.html', '']
TESTI += ['--- ADESIONE ---',
          'Un programma nato dalle lotte. Fuori dal centrodestra, fuori dal «campo largo».',
          'Lascia i tuoi contatti: ti scriviamo per gli incontri nella tua provincia.',
          f'{SITO["indirizzo"].rstrip("/")}/aderisci.html', '']

(QUI / 'social-testi.txt').write_text('\n'.join(TESTI), encoding='utf-8')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit('Serve Playwright: pip install playwright --break-system-packages && playwright install chromium')

lavori = []
for p in P:
    for forma in MISURE:
        lavori.append((f'SA-social-{p["numero"]}-{forma}.png', pilastro(p, forma), forma))
for forma in MISURE:
    lavori.append((f'SA-social-aderisci-{forma}.png', adesione(forma), forma))

for nome, html, _ in lavori:
    (QUI / f'_{nome}.html').write_text(html, encoding='utf-8')

gestore = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(RADICE))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 8932), gestore)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for nome, _, forma in lavori:
            w, h = MISURE[forma]
            pg = b.new_page(viewport={'width': w, 'height': h})
            pg.goto(f'http://127.0.0.1:8932/stampa/_{nome}.html')
            pg.wait_for_timeout(400)
            pg.locator('.tela').screenshot(path=str(USCITA / nome))
            pg.close()
        b.close()
finally:
    server.shutdown()

for nome, _, _ in lavori:
    (QUI / f'_{nome}.html').unlink()

zip_ = RADICE / 'risorse' / 'materiali' / 'SA-social-kit.zip'
with zipfile.ZipFile(zip_, 'w', zipfile.ZIP_DEFLATED) as z:
    for nome, _, _ in lavori:
        z.write(USCITA / nome, f'immagini/{nome}')
    z.write(QUI / 'social-testi.txt', 'testi-pronti.txt')
    z.write(RADICE / 'risorse' / 'materiali' / 'SA-volantino-A5-nero.pdf', 'volantino-A5-nero.pdf')
print(f'{len(lavori)} immagini · {zip_.name}: {zip_.stat().st_size // 1024} KB')
