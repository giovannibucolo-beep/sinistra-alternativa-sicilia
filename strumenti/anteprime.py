#!/usr/bin/env python3
"""Disegna le immagini di anteprima per i social (1200x630) in risorse/og/.
Serve Chrome con Playwright: si lancia a mano quando cambia un titolo, non a ogni pubblicazione.
"""
import base64, pathlib, re, sys
from playwright.sync_api import sync_playwright
QUI = pathlib.Path(__file__).parent.parent; RIS = QUI / 'risorse'; OG = RIS / 'og'; OG.mkdir(exist_ok=True)
U = lambda n: 'data:image/svg+xml;base64,' + base64.b64encode((RIS / 'loghi' / n).read_bytes()).decode()
F = lambda w: 'data:font/woff2;base64,' + base64.b64encode((RIS / 'font' / f'montserrat-latin-{w}-normal.woff2').read_bytes()).decode()
SA = f"<img class=sa src='{U('sa-monogramma-negativo-su-nero.svg')}'>"   # REGOLA: «SA» è il simbolo
voci = [('generale', 'Regionali 2027', f'La Sicilia che {SA}', 'Un programma nato dalle lotte. Aderisci al coordinamento.')]
for f in sorted((QUI / 'contenuti' / 'pilastri').glob('*.md')):
    t = f.read_text(encoding='utf-8'); g = lambda k: re.search(rf'^{k}: (.*)$', t, re.M).group(1)
    voci.append(('pilastro-' + g('numero'), f"Pilastro {g('numero')} · La Sicilia che {SA}", g('verbo'), g('slogan')))
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--no-sandbox'])
    for nome, occ, tit, sotto in voci:
        pg = b.new_page(viewport={'width': 1200, 'height': 630})
        pg.set_content(f"""<style>@font-face{{font-family:M;font-weight:900;src:url({F(900)})}}@font-face{{font-family:M;font-weight:700;src:url({F(700)})}}
body{{margin:0;width:1200px;height:630px;display:flex;background:#000;color:#fff;font-family:M;overflow:hidden}}
.sx{{flex:0 0 430px;display:flex;align-items:center;justify-content:center;background:#EC3657;clip-path:polygon(0 0,100% 0,82% 100%,0 100%)}}.sx img{{width:330px;margin-right:36px}}
.dx{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:18px;padding:0 60px 0 24px}}.k{{font-weight:900;font-size:24px;letter-spacing:4px;text-transform:uppercase;color:#EC3657}}
img.sa{{height:1.06em;vertical-align:baseline;margin:0 .06em}}h1{{margin:0;font-weight:900;font-size:{66 if 'img' in tit else 74 if len(tit) < 20 else 60}px;white-space:{'nowrap' if 'img' in tit else 'normal'};line-height:.98;text-transform:uppercase}}p{{margin:0;font-weight:700;font-size:30px;line-height:1.25}}</style>
<div class=sx><img src="{U('sa-contrassegno.svg')}"></div><div class=dx><span class=k>{occ}</span><h1>{tit}</h1><p>{sotto}</p></div>""")
        pg.wait_for_timeout(500); pg.screenshot(path=str(OG / f'{nome}.png')); pg.close()
    b.close()
print('anteprime:', len(voci))
