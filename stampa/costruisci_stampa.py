#!/usr/bin/env python3
"""Costruisce volantino e manifesto a partire dagli stessi contenuti del sito.

Tre versioni di colore per ciascuno — nero, bianco, rosso — così la scelta si fa guardando,
non immaginando. Scrive gli HTML in `stampa/` e i PDF per la tipografia in `risorse/materiali/`.
Misure in millimetri reali. Serve `segno` per il codice QR e Playwright con Chrome per i PDF.
"""
import json, pathlib, re, subprocess, sys, time

QUI = pathlib.Path(__file__).resolve().parent
RADICE = QUI.parent
SITO = json.loads((RADICE / 'contenuti' / 'sito.json').read_text(encoding='utf-8'))
COMMITTENTE = SITO['committente'] if SITO['committente'] != 'nome da indicare' else 'COMMITTENTE RESPONSABILE DA INDICARE'
INDIRIZZO = SITO['indirizzo'].replace('https://', '').rstrip('/')
USCITA = RADICE / 'risorse' / 'materiali'

P = []
for f in sorted((RADICE / 'contenuti' / 'pilastri').glob('*.md')):
    P.append(dict(re.findall(r'^([a-z_]+): (.*)$', f.read_text(encoding='utf-8').split('---')[1], re.M)))

QR = QUI / 'qr-aderisci.svg'
try:
    import segno
    segno.make(SITO['indirizzo'].rstrip('/') + '/aderisci.html', error='m').save(str(QR), kind='svg', scale=10, border=2, dark='#000', light=None)
except ImportError:
    print('segno non installato: il codice QR non è stato rigenerato')

TEMI = {
    'nero':   {'fondo': '#000000', 'testo': '#ffffff', 'acc': '#EC3657', 'riga': 'rgba(255,255,255,.22)', 'contr': 'sa-contrassegno.svg',                  'mono': 'sa-monogramma-bianco.svg', 'nota': 'rgba(255,255,255,.75)'},
    'bianco': {'fondo': '#ffffff', 'testo': '#000000', 'acc': '#B01030', 'riga': '#D8D0D2',               'contr': 'sa-contrassegno.svg',                  'mono': 'sa-monogramma.svg',        'nota': 'rgba(0,0,0,.6)'},
    'rosso':  {'fondo': '#B01030', 'testo': '#ffffff', 'acc': '#ffffff', 'riga': 'rgba(255,255,255,.32)', 'contr': 'sa-contrassegno-negativo-su-nero.svg', 'mono': 'sa-monogramma-bianco.svg', 'nota': 'rgba(255,255,255,.8)'},
}

BASE_STILE = '''
@font-face { font-family: Montserrat; font-weight: 500; src: url(../risorse/font/montserrat-latin-500-normal.woff2) format("woff2"); }
@font-face { font-family: Montserrat; font-weight: 700; src: url(../risorse/font/montserrat-latin-700-normal.woff2) format("woff2"); }
@font-face { font-family: Montserrat; font-weight: 800; src: url(../risorse/font/montserrat-latin-800-normal.woff2) format("woff2"); }
@font-face { font-family: Montserrat; font-weight: 900; src: url(../risorse/font/montserrat-latin-900-normal.woff2) format("woff2"); }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Montserrat, sans-serif; font-weight: 500; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
ul { list-style: none; }
.faccia { position: relative; overflow: hidden; page-break-after: always; break-after: page; }
.faccia:last-child { page-break-after: auto; break-after: auto; }
.committente { font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
'''


def scrivi(nome, corpo, stile):
    f = QUI / nome
    f.write_text(f'<!DOCTYPE html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n<title>{nome}</title>\n<style>{BASE_STILE}{stile}</style>\n</head>\n<body>\n{corpo}\n</body>\n</html>\n', encoding='utf-8')
    return f


def volantino(t):
    c = TEMI[t]
    verbi = ''.join(f'<li>{p["verbo"]}</li>' for p in P)
    righe = ''.join(f'<li><i>{p["numero"]}</i><b>{p["titolo"]}</b><span>{p["slogan"]}</span></li>' for p in P)
    corpo = f'''<section class="faccia fronte">
  <img class="contr" src="../risorse/loghi/{c["contr"]}" alt="">
  <h1>La Sicilia che <img src="../risorse/loghi/{c["mono"]}" alt="SA"></h1>
  <ul class="verbi">{verbi}</ul>
  <p class="claim">Un programma nato dalle lotte.<br>Fuori dal centrodestra, fuori dal «campo largo».</p>
  <p class="sito">{INDIRIZZO}</p>
</section>
<section class="faccia retro">
  <p class="occhiello">Il programma in sette punti</p>
  <ul class="pilastri">{righe}</ul>
  <div class="due-binari"><b>Come si legge:</b> ogni punto dice che cosa può fare la Regione subito e che cosa va strappato allo Stato. Non promettiamo ciò che la Regione non può fare.</div>
  <div class="aderisci">
    <div><p class="k">Aderisci</p><p class="grande">Lascia i tuoi contatti: ti scriviamo per gli incontri nella tua provincia.</p><p class="sito2">{INDIRIZZO}/aderisci.html</p></div>
    <img class="qr" src="qr-aderisci.svg" alt="Codice QR verso la pagina di adesione">
  </div>
  <p class="committente">{COMMITTENTE}</p>
</section>'''
    stile = f'''
@page {{ size: 148mm 210mm; margin: 0; }}
.faccia {{ width: 148mm; height: 210mm; color: {c["testo"]}; background: {c["fondo"]}; }}
.retro {{ color: #000; background: #fff; }}
.fronte {{ display: flex; flex-direction: column; align-items: center; padding: 13mm 12mm 9mm; text-align: center; }}
.fronte .contr {{ width: 52mm; height: 52mm; }}
.fronte h1 {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 1mm 3mm; margin-top: 7mm; font-size: 11.4mm; font-weight: 900; line-height: 1; text-transform: uppercase; letter-spacing: -.01em; }}
.fronte h1 img {{ width: 27mm; }}
.verbi {{ margin-top: 8mm; font-size: 6.1mm; font-weight: 800; line-height: 1.5; text-transform: uppercase; }}
.verbi li + li {{ border-top: .3mm solid {c["riga"]}; }}
.claim {{ margin-top: auto; padding-top: 4mm; font-size: 4.4mm; font-weight: 700; line-height: 1.45; color: {c["acc"]}; }}
.sito {{ width: 100%; margin-top: 5mm; padding-top: 4mm; border-top: 1mm solid {c["acc"]}; font-size: 3.9mm; font-weight: 900; line-height: 1.3; letter-spacing: .02em; overflow-wrap: anywhere; }}
.retro {{ display: flex; flex-direction: column; padding: 12mm 12mm 8mm; }}
.occhiello {{ font-size: 3.4mm; font-weight: 800; letter-spacing: .22em; text-transform: uppercase; color: #B01030; }}
.pilastri {{ margin-top: 5mm; }}
.pilastri li {{ display: grid; grid-template-columns: 9mm 1fr; gap: 0 2mm; padding: 2.6mm 0; border-bottom: .3mm solid #D8D0D2; }}
.pilastri i {{ grid-row: span 2; font-size: 7mm; font-weight: 900; font-style: normal; line-height: 1; color: {c["acc"] if t != "bianco" else "#EC3657"}; }}
.pilastri b {{ font-size: 4.4mm; font-weight: 900; text-transform: uppercase; }}
.pilastri span {{ font-size: 3.5mm; line-height: 1.35; }}
.due-binari {{ margin-top: 4mm; padding: 3mm; font-size: 3.3mm; line-height: 1.4; background: #FDE7EB; }}
.aderisci {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 5mm; margin-top: auto; padding-top: 5mm; border-top: 1mm solid #000; }}
.aderisci .k {{ font-size: 7mm; font-weight: 900; line-height: 1; text-transform: uppercase; color: #EC3657; }}
.aderisci .grande {{ max-width: 62mm; margin-top: 1.5mm; font-size: 3.4mm; line-height: 1.35; }}
.aderisci .sito2 {{ margin-top: 2mm; font-size: 3.6mm; font-weight: 900; }}
.aderisci .qr {{ width: 30mm; height: 30mm; }}
.committente {{ margin-top: 4mm; font-size: 2.5mm; color: rgba(0,0,0,.6); }}
'''
    return corpo, stile


def manifesto(t):
    c = TEMI[t]
    corpo = f'''<section class="faccia">
  <img class="contr" src="../risorse/loghi/{c["contr"]}" alt="">
  <h1>La Sicilia che <img src="../risorse/loghi/{c["mono"]}" alt="SA"></h1>
  <ul class="verbi">{''.join(f'<li>{p["verbo"]}</li>' for p in P[:4])}</ul>
  <p class="claim">Un programma nato dalle lotte</p>
  <div class="fondo"><img class="qr" src="qr-aderisci.svg" alt="Codice QR verso la pagina di adesione"><div><p class="inquadra">Inquadra e aderisci</p><p class="sito">{INDIRIZZO}</p></div></div>
  <p class="committente">{COMMITTENTE}</p>
</section>'''
    stile = f'''
@page {{ size: 700mm 1000mm; margin: 0; }}
.faccia {{ display: flex; flex-direction: column; align-items: center; width: 700mm; height: 1000mm; padding: 42mm 45mm 34mm; text-align: center; color: {c["testo"]}; background: {c["fondo"]}; }}
.contr {{ width: 262mm; height: 262mm; }}
h1 {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 2mm 14mm; margin-top: 26mm; font-size: 64mm; font-weight: 900; line-height: .95; text-transform: uppercase; letter-spacing: -.015em; }}
h1 img {{ width: 175mm; }}
.verbi {{ margin-top: 20mm; font-size: 30mm; font-weight: 800; line-height: 1.34; text-transform: uppercase; }}
.claim {{ margin-top: 18mm; font-size: 21mm; font-weight: 700; color: {c["acc"]}; }}
.fondo {{ display: flex; align-items: center; gap: 16mm; width: 100%; margin-top: auto; padding-top: 12mm; border-top: 4mm solid {c["acc"]}; text-align: left; }}
.fondo .qr {{ width: 85mm; height: 85mm; padding: 4mm; background: #fff; }}
.inquadra {{ font-size: 15mm; font-weight: 800; text-transform: uppercase; color: {c["acc"]}; }}
.sito {{ font-size: 13mm; font-weight: 900; line-height: 1.25; overflow-wrap: anywhere; }}
.committente {{ margin-top: 12mm; font-size: 6mm; color: {c["nota"]}; }}
'''
    return corpo, stile


FATTI = []
for t in TEMI:
    FATTI.append((scrivi(f'volantino-A5-{t}.html', *volantino(t)), f'SA-volantino-A5-{t}.pdf', '148mm', '210mm'))
    FATTI.append((scrivi(f'manifesto-70x100-{t}.html', *manifesto(t)), f'SA-manifesto-70x100-{t}.pdf', '700mm', '1000mm'))
print('scritti', len(FATTI), 'file HTML')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit('Playwright non installato: i PDF non sono stati generati (gli HTML sì).')
porta = 8799
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(porta)], cwd=RADICE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1.2)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='chrome', args=['--no-sandbox'])
        pg = b.new_page()
        for f, nome, larg, alt in FATTI:
            pg.goto(f'http://127.0.0.1:{porta}/stampa/{f.name}')
            pg.wait_for_timeout(1400)
            pg.pdf(path=str(USCITA / nome), width=larg, height=alt, print_background=True, margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'})
            print(f'{nome}: {(USCITA / nome).stat().st_size // 1024} KB')
        b.close()
finally:
    srv.terminate()
