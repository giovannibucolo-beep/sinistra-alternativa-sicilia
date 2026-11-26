#!/usr/bin/env python3
"""Apre ogni pagina a misura telefono e computer: sbordi orizzontali, tasti troppo piccoli, errori di script. Serve Playwright."""
import pathlib, json, sys, http.server, threading, functools
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(__file__).parent.parent / 'pubblico'
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8791), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))); srv.RequestHandlerClass.log_message = lambda *a: None
threading.Thread(target=srv.serve_forever, daemon=True).start()
guai = 0
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--no-sandbox'])
    for f in sorted(OUT.rglob('*.html')):
        nome = str(f.relative_to(OUT))
        if nome == '404.html': continue   # usa indirizzi assoluti: si prova solo in linea
        for et, w, h in [('tel', 390, 844), ('pc', 1440, 900)]:
            pg = b.new_page(viewport={'width': w, 'height': h}); err = []; pg.on('pageerror', lambda e: err.append(str(e))); pg.on('requestfailed', lambda r: err.append('non caricato: ' + r.url) if '/risorse/img/' not in r.url else None)
            pg.goto('http://127.0.0.1:8791/' + nome); pg.wait_for_timeout(250)
            r = pg.evaluate('''()=>{const W=innerWidth;const fuori=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>W+1||r.left<-1)&&!e.closest('.salta')&&!e.closest('.menu:not(.aperto)')}).slice(0,3).map(e=>e.tagName+'.'+e.className);
              const picc=[...document.querySelectorAll('main a.btn, main button, .menu-b, main input, main select, .mappa a, a.evento, a.scheda, .striscia a')].filter(e=>{const r=e.getBoundingClientRect();return r.height>0&&r.height<44}).map(e=>(e.textContent||e.name||'').trim().slice(0,18)+':'+Math.round(e.getBoundingClientRect().height));
              return {sw:document.documentElement.scrollWidth,W,fuori,picc}}''')
            if r['sw'] > r['W'] or r['fuori'] or r['picc'] or err: guai += 1; print(nome, et, json.dumps(r, ensure_ascii=False), err)
            pg.close()
    b.close()
print('pagine con problemi:', guai); sys.exit(1 if guai else 0)
